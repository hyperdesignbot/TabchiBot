from pyrogram import Client,Filters, errors
from redis import StrictRedis
from configparser import ConfigParser
from time import sleep
from os import path
import random
from pyrogram.errors import (
    BadRequest, Flood, InternalServerError,
    SeeOther, Unauthorized, UnknownError, FloodWait
)
import _thread
import schedule
config = ConfigParser()
if path.isfile("./config.ini"):
    config.read("config.ini")
else:
    api_id = input("Please Input ApiId : ")
    api_hash = input("Please Input ApiHash : ")
    config["pyrogram"] = {
        'api_id': api_id,
        'api_hash': api_hash,
    }
    gplog = input("Please Input Group Log : ")
    sudo = input("Please Input Sudo Users : ")
    tabchi = input("Please input Tabchi Id : ")
    DB = input("Please input DB number : ")
    session_name = 'tabchi%s'%tabchi[:4]
    config["tabchi"] = {
        'gplog': gplog,
        'sudo': sudo,
        'tabchi': tabchi,
        'DB': DB,
        'session_name': session_name
    }
    with open("config.ini", "w") as configfile:
        config.write(configfile)
    r = StrictRedis(host="localhost", port=6379, decode_responses=True, db=int(DB))
    r.set("data:power", "off")
    r.set("data:gp_get_post", config["tabchi"]["gplog"])
    r.lpush("data:correct_group", " ")
    r.set("data:min_gp_member", "10")
    r.set("data:max_gp_member", "1000")
    r.set("data:msgid_of_baner", "1")
    r.lpush("gp_ids", config["tabchi"]["gplog"])


db_num = int(config["tabchi"]["DB"])
db = StrictRedis(host="localhost", port=6379, decode_responses=True, db=db_num)
app = Client(session_name=config["tabchi"]["session_name"],config_file="./config.ini")
gplog = int(config["tabchi"]["gplog"])
tabchi = config["tabchi"]["tabchi"].split(" ")
sudo = config["tabchi"]["sudo"]
app.start()


def sndgplog(text):
    app.send_message(gplog, text, parse_mode="MarkDown",disable_web_page_preview=True)

print("Bot Now Running")
sndgplog("Bot Now Running")

@app.on_message(Filters.private)
def private_received(client, m):
    chat_id = m.chat.id
    msg_text = m.text
    if chat_id == int(sudo):
        if msg_text.startswith('https://t.me/joinchat/') or msg_text.startswith('https://telegram.me/joinchat'):
            try:
                joining(msg_text)
            except errors.exceptions.bad_request_400.UserAlreadyParticipant:
                app.send_message(chat_id,'تبچی قبلا عضو گروه %s بوده است'%msg_text)
            except Exception as e:
                app.send_message(chat_id,'لینک گروه صحیح نیست')
                sndgplog(str(e))

        elif msg_text.startswith('min '):
            _, min_gp_member = msg_text.split(' ')
            if min_gp_member.isdigit():
                app.send_message(chat_id,'حداقل تعداد اعضای سوپرگروه به %s تغییر یافت'%min_gp_member)
                db.set("data:min_gp_member",min_gp_member)
            else:
                app.send_message(chat_id,'دستور صحیح نیست')
        elif msg_text.startswith('max'):
            _, max_gp_member = msg_text.split(' ')
            if max_gp_member.isdigit():
                app.send_message(chat_id,'حداکثر تعداد اعضای سوپرگروه به %s تغییر یافت'%max_gp_member)
                db.set("data:max_gp_member", max_gp_member)
            else:
                app.send_message(chat_id,'دستور صحیح نیست')
        elif msg_text == 'on':
            app.send_message(chat_id,'ربات به on تغییر یافت')
            db.set("data:power", "on")
        elif msg_text == 'off':
            app.send_message(chat_id,'ربات به off تغییر یافت')
            db.set("data:power", "off")
        elif msg_text.startswith("gpslink"):
            links = db.lrange('data:correct_group',0,-1)
            app.send_message(chat_id,links)
        elif msg_text == 'help':
            text_help = ('\n'
                         ' 1️⃣ دریافت لینک های سالم:\n'
                         'gpslink\n'
                         '2️⃣ غیرفعال کردن مینیم و ماکزیمم\n'
                         'off\n'
                         '3️⃣ فعال کردن مینیمم و ماکزیمم گروه\n'
                         'on\n'
                         '\n'
                         '4️⃣ تعیین مینیمم اعضای گروه:\n'
                         'min 100\n'
                         '5️⃣ تعیین ماکزیمم اعضای گروه\n'
                         'max 1000\n'
                         '\n'
                         '')
            app.send_message(chat_id,text_help)
    else:
        msg_other = ('سورس اختصاصی برای :\n'
                     '@fuck_net01\n'
                     '')
        app.send_message(chat_id,msg_other)
def auotopostjob():
    _thread.start_new(autopost,())
    print("start thread auto post")
def autopost():
    print('auto post')
    gp_ids = db.lrange('gp_ids', 0, -1)
    baner_text = db.get("data:banertxt")
    for gpid in gp_ids:
        m = random.randrange(120)
        sndgplog("sleep %s second in post msg" % m)
        sleep(m)
        try:
            app.send_message(int(gpid), baner_text)
        except errors.exceptions.bad_request_400.ChannelPrivate:
            index = gp_ids.index(gpid)
            db.lrem('gp_ids', index, gpid)
        except errors.exceptions.forbidden_403.ChatWriteForbidden:
            index = gp_ids.index(gpid)
            db.lrem('gp_ids', index, gpid)
        except FloodWait as e:
            print(f"Bot Has Been ShutDown For {e.x} Seconds")
            sleep(e.x)
        except BadRequest as e:
            print(e)
            sndgplog(str(e))
        except Flood as e:
            print(e)
            sndgplog(str(e))
        except InternalServerError as e:
            print(e)
            sndgplog(str(e))
        except SeeOther as e:
            print(e)
            sndgplog(str(e))
        except Unauthorized as e:
            print(e)
            sndgplog(str(e))
        except UnknownError as e:
            print(e)
            sndgplog(str(e))
def autofwd():
    print('auto fwd2')
    gp_ids = db.lrange('gp_ids', 0, -1)
    source_group = db.get("data:gp_get_post")
    msg_id = db.get("data:msgid_of_baner")
    for gpid in gp_ids:
        m = random.randrange(120)
        sndgplog("sleep %s second in forward msg" % m)
        sleep(m)
        try:
            app.forward_messages(int(gpid), int(source_group), int(msg_id))
        except errors.exceptions.bad_request_400.ChannelPrivate:
            index = gp_ids.index(gpid)
            db.lrem('gp_ids', index, gpid)
        except errors.exceptions.forbidden_403.ChatWriteForbidden:
            index = gp_ids.index(gpid)
            db.lrem('gp_ids', index, gpid)
        except FloodWait as e:
            print(f"Bot Has Been ShutDown For {e.x} Seconds")
            sleep(e.x)
        except BadRequest as e:
            print(e)
            sndgplog(str(e))
        except Flood as e:
            print(e)
            sndgplog(str(e))
        except InternalServerError as e:
            print(e)
            sndgplog(str(e))
        except SeeOther as e:
            print(e)
            sndgplog(str(e))
        except Unauthorized as e:
            print(e)
            sndgplog(str(e))
        except UnknownError as e:
            print(e)
            sndgplog(str(e))
def joining(join_link):
    power = db.get("data:power")
    if power == 'off':
        try:
            app.join_chat(join_link)
            db.lpush('data:correct_group', join_link)
            app.send_message(sudo, "به گروه %s جوین شد و لینک گروه ثبت شد" % join_link)
        except FloodWait as e:
            sndgplog(f"Bot Has Been ShutDown For {e.x} Seconds")
            sleep(e.x)

    elif power == 'on':
        count_members = app.get_chat(join_link)["members_count"]
        max_mem = db.get("data:max_gp_member")
        min_mem = db.get("data:min_gp_member")
        if int(min_mem) <= int(count_members) <= int(max_mem):
            try:
                app.join_chat(join_link)
                db.lpush('data:correct_group', join_link)
                app.send_message(sudo, "به گروه %s جوین شد و لینک گروه ثبت شد" % join_link)
            except FloodWait as e:
                sndgplog(f"Bot Has Been ShutDown For {e.x} Seconds")
                sleep(e.x)
        else:
            app.send_message(sudo,"تعداد اعضای گروه خارج از تعداد تعیین شده است.\n گروه:%s  \n تعداد اعضا: %s"%(join_link,count_members))

@app.on_message(Filters.group)
def group_received(client,m):
    gp_get_post = db.get("data:gp_get_post")
    list_gp_ids = db.lrange('gp_ids',0,-1)
    if str(m.chat.id) not in list_gp_ids:
        db.lpush('gp_ids',m.chat.id)
    if str(m.chat.id) == gp_get_post:
        print(m.text)
        db.set("data:msgid_of_baner",m.message_id)
        if m.text:
            db.set("data:banertxt",m.text)
        print(m.message_id)
        autofwd()
    if m.text:
        if m.text.startswith('https://t.me/joinchat/'):
            try:
                joining(m.text)
            except Exception as e:
                e = 'joinchat %s'%str(e)
                sndgplog(str(e))


schedule.every(1).minutes.do(autopostjob())
while 1:
    schedule.run_pending()
    sleep(1)
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
import re
import json
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
    r.set("tabchi:power", "off")
    r.set("tabchi:gp_get_post", config["tabchi"]["gplog"])
    r.lpush("tabchi:correct_group", " ")
    r.set("tabchi:min_gp_member", "10")
    r.set("tabchi:max_gp_member", "1000")
    r.set("tabchi:msgid_of_baner", "1")
    r.lpush("gp_ids", config["tabchi"]["gplog"])


db_num = int(config["tabchi"]["DB"])
db = StrictRedis(host="localhost", port=6379, decode_responses=True, db=db_num)
db.set("tabchi:power", "off")
db.set("tabchi:gp_get_post", config["tabchi"]["gplog"])
db.lpush("tabchi:correct_group", " ")
db.set("tabchi:min_gp_member", "10")
db.set("tabchi:max_gp_member", "1000")
db.set("tabchi:msgid_of_baner", "1")
db.lpush("gp_ids", config["tabchi"]["gplog"])
app = Client(session_name=config["tabchi"]["session_name"],config_file="./config.ini")
gplog = int(config["tabchi"]["gplog"])
tabchi = config["tabchi"]["tabchi"].split(" ")
sudo = config["tabchi"]["sudo"]
app.start()


def sndgplog(text):
    app.send_message(gplog, text, parse_mode="MarkDown",disable_web_page_preview=True)
def load_data(fname):
    try:
        f = open(fname, "rb")
        return json.loads(f.read())
    except Exception as e:
        print(e)
        return []


def save_data(fname, data):
    f = open(fname, "w")
    f.write(json.dumps(data))
    f.close()

print("Bot Now Running")
sndgplog("Bot Now Running")

@app.on_message(Filters.incoming)
def incoming_received(client, m):
    try:
        chat_id = m.chat.id
        entities = m['entities'] if m["entities"] else m["caption_entities"]
        text = m.text if m.text else m.caption
        if entities:
            urls = []
            for i in entities:
                if i['type'] == "url":
                    if re.findall("(t|telegram|tlgrm)(\.)(me|org|dog)(/)(joinchat)(/)(.{22})", text):
                        r = re.findall("(t|telegram|tlgrm)(\.)(me|org|dog)(/)(joinchat)(/)(.{22})", text)
                        for v in r:
                            url = 'https://' + ''.join(v)
                            links = load_data("./links.json")
                            if url not in links:
                                links.append(url)
                                urls.append(url)
                                save_data("./links.json", links)
            for item in urls:
                print('join link is:',item)
                joining(item)
        if chat_id == int(sudo):
            print("in private sudo")
            if text.startswith('min '):
                _, min_gp_member = text.split(' ')
                if min_gp_member.isdigit():
                    app.send_message(chat_id,'حداقل تعداد اعضای سوپرگروه به %s تغییر یافت'%min_gp_member)
                    db.set("tabchi:min_gp_member",min_gp_member)
                else:
                    app.send_message(chat_id,'دستور صحیح نیست')
            elif text.startswith('max'):
                _, max_gp_member = text.split(' ')
                if max_gp_member.isdigit():
                    app.send_message(chat_id,'حداکثر تعداد اعضای سوپرگروه به %s تغییر یافت'%max_gp_member)
                    db.set("tabchi:max_gp_member", max_gp_member)
                else:
                    app.send_message(chat_id,'دستور صحیح نیست')
            elif text == 'on':
                app.send_message(chat_id,'ربات به on تغییر یافت')
                db.set("tabchi:power", "on")
            elif text == 'off':
                app.send_message(chat_id,'ربات به off تغییر یافت')
                db.set("tabchi:power", "off")
            elif text.startswith("gpslink"):
                links = db.lrange('tabchi:correct_group',0,-1)
                app.send_message(chat_id,links)
            elif text == 'gozaresh':
                all = len(db.smembers("tabchi:all"))
                pv = len(db.smembers("tabchi:Pvs"))
                gps = len(db.smembers("tabchi:gps"))
                Sgps = len(db.smembers("tabchi:Sgps"))
                gtext = ('\n'
                         'ALL : %s\n'
                         'PV : %s\n'
                         'Groups: %s\n'
                         'Supergroups : %s\n'
                         '') % (all, pv, gps, Sgps)
                app.send_message(chat_id,gtext)
            elif text == 'help':
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
                             '6️⃣ گزارش \n'
                             'gozaresh \n'
                             '- ربات تبچی اختصاصی برای 👇\n'
                             '● @Fuck_net01')
                app.send_message(chat_id,text_help)
            else:
                if not entities:
                    app.send_message(chat_id,'جهت دیدن دستورات عبارت help را وارد کنید')
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
def autopost():
    gp_ids = db.lrange('gp_ids', 0, -1)
    baner_text = db.get("tabchi:banertxt")
    for gpid in gp_ids:
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
    source_group = db.get("tabchi:gp_get_post")
    banerid = db.get("tabchi:msgid_of_baner")
    itemids = db.smembers("tabchi:all")
    success_list = []
    for itemid in itemids:
        try:
            app.forward_messages(int(itemid), int(source_group), int(banerid))
            success_list.append(itemid)
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
    failed = len(db.smembers("tabchi:all")) - len(success_list)
    success = len(success_list)
    app.send_message(sudo,'Forward finish \n %s suceessful\n %s Failed'%(success,failed))

def joining(join_link):
    print("in joining")
    power = db.get("tabchi:power")
    print("power",power)
    if power == 'off':
        print("in power off")
        app.join_chat(join_link)
        print("after joining")
        db.lpush('tabchi:correct_group', join_link)
        app.send_message(sudo, "به گروه %s جوین شد و لینک گروه ثبت شد" % join_link)
    elif power == 'on':
        print("in power on")
        count_members = app.get_chat(join_link)["members_count"]
        print("count:",count_members)
        max_mem = db.get("tabchi:max_gp_member")
        min_mem = db.get("tabchi:min_gp_member")
        print("max: ",max_mem,"min: ",min_mem)
        if int(min_mem) <= int(count_members) <= int(max_mem):
            print("in min and max")
            app.join_chat(join_link)
            print("after join max min")
            db.lpush('tabchi:correct_group', join_link)
            app.send_message(sudo, "به گروه %s جوین شد و لینک گروه ثبت شد" % join_link)
        else:
            print("not in limit")
            app.send_message(sudo,"تعداد اعضای گروه خارج از تعداد تعیین شده است.\n گروه:%s  \n تعداد اعضا: %s"%(join_link,count_members))

@app.on_message(Filters.group)
def group_received(client,m):
    gp_get_post = db.get("tabchi:gp_get_post")
    if str(m.chat.id) == gp_get_post:
        print("in get post")
        db.set("tabchi:msgid_of_baner",m.message_id)
        if m.text:
            db.set("tabchi:banertxt",m.text)
        app.send_message(m.chat.id,'پست جهت فوروارد ذخیره شد')
        autofwd()
    if str(m.chat.id)[:4] == '-100':
        db.sadd("tabchi:Sgps", m.chat.id)
        db.sadd("tabchi:all", m.chat.id)
    else:
        db.sadd("tabchi:gps", m.chat.id)
        db.sadd("tabchi:all", m.chat.id)

@app.on_message(filters=Filters.private & Filters.incoming)
def private(client, m):
    db.sadd("tabchi:Pvs", m.chat.id)
    db.sadd("tabchi:all", m.chat.id)


schedule.every(3).hours.do(autofwd)
while 1:
    schedule.run_pending()
    sleep(1)
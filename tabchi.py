from pyrogram import Client,Filters, errors
from redis import StrictRedis
from configparser import ConfigParser
from os import path
config = ConfigParser()
if path.isfile("./config.ini"):
    config.read("config.ini")
else:
    api_id = input("Please Input ApiId : ")
    api_hash = input("Please Input ApiHash : ")
    phone = input("Please Input Phone Number : ")
    config["pyrogram"] = {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone_number': phone,
    }
    gplog = input("Please Input Group Log : ")
    sudo = input("Please Input Sudo Users : ")
    tabchi = input("Please input Tabchi Id : ")
    DB = input("Please Input DB Number : ")
    session_name = input("Please Input Session Name : ")
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
    r.set("data:correct_group", " ")
    r.set("data:min_gp_member", "10")
    r.set("data:max_gp_member", "1000")
    r.set("data:msgid_of_baner", "1")
    r.set("gp_ids", config["tabchi"]["gplog"])

db_num = int(config["tabchi"]["DB"])
db = StrictRedis(host="localhost", port=6379, decode_responses=True, db=db_num)
app = Client(session_name=config["tabchi"]["session_name"],config_file="./config.ini")
gplog = int(config["tabchi"]["gplog"])
tabchi = config["tabchi"]["tabchi"].split(" ")
sudo = config["tabchi"]["sudo"]
app.start()


def sndgplog(text):
    app.send_message(gplog, text, parse_mode="MarkDown")

print("Bot Now Running")
sndgplog("Bot Now Running")

@app.on_message(Filters.private)
def private_received(client, m):
    chat_id = m.chat.id
    msg_text = m.text
    if chat_id == sudo:
        if msg_text.startswith('https://t.me/joinchat/'):
            try:
                app.join_chat(msg_text)
                db.lpush('data:correct_group',msg_text)
            except Exception as e:
                app.send_message(chat_id, 'لینک گروه صحیح نیست')
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
def fwd_msg():
    gp_ids_1 = db.lrange('gp_ids', 0, -1)
    gp_ids = [-483235719,-1001434046797]
    source_group = db.get("data:gp_get_post")
    msg_id = db.get("data:msgid_of_baner")
    power = db.get("data:power")
    if power == 'off':
        for gpid in gp_ids:
            try:
                app.forward_messages(gpid, source_group, msg_id)
            except Exception as e:
                sndgplog(str(e))
    else:
        for gpid in gp_ids:
            count_members = app.get_chat_members_count(int(gpid))
            max_mem = db.get("data:max_gp_member")
            min_mem = db.get("data:min_gp_member")
            if int(min_mem) <= count_members <= int(max_mem):
                try:
                    app.forward_messages(gpid,source_group,msg_id)
                except Exception as e:
                    sndgplog(str(e))

@app.on_message(Filters.group)
def group_received(client,m):
    print('test power:',db.get("data:power"))
    gp_get_post = db.get("data:gp_get_post")
    list_gp_ids = db.lrange('gp_ids',0,-1)
    if str(m.chat.id) not in list_gp_ids:
        db.lpush('gp_ids',m.chat.id)
    if str(m.chat.id) == gp_get_post:
        db.set("data:msgid_of_baner",m.message_id)
        fwd_msg()
    #if m.text:
        #if m.text.startswith('https://t.me/joinchat/'):
            #print(m.text)
        #try:
            #app.join_chat(m.text)
            #db.lpush('data:correct_group', m.text)
        #except Exception as e:
            #sndgplog(str(e))




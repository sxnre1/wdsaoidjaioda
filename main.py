from http.client import FOUND
import discord
import sqlite3
import requests
from setting import *
import uuid
from datetime import timedelta
import datetime
from json import JSONDecodeError
import asyncio
import randomstring
from discord import ui
from urllib.parse import quote

AUTH_LINK = "https://restore.cloud-mkt.xyz/join"
API_ENDPOINT = 'https://discord.com/api/v9'

intents = discord.Intents.all()
client = discord.Client(intents=intents)
owner = 1013066318456561785
client_id = CLIENT_ID
client_secret = CLIENT_SECRET

async def refresh_token(refresh_token):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    print(r.json())
    return False if "error" in r.json() else r.json()

def get_expiretime(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간 " + str(round(minutes)) + "분" 
    else:
        return False

async def add_user(token, gid,id):
    while True:
        jsonData = {"access_token" : token}
        header = {"Authorization": "Bot " + BOT_TOKEN} #Bot Token
        r = requests.put(f"{API_ENDPOINT}/guilds/{gid}/members/{id}", json=jsonData, headers=header)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    if (r.status_code == 201 or r.status_code == 204):
        return True
    else:
        print(r.json())
        return False

def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

async def register_redirect_url(id):
    return True

def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

async def is_guild(id):
    con,cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True
    
def embeda(embedtype, embedtitle, description):
    container = ui.Container()

    if embedtype == "error":
        text_style = "❌ "
    elif embedtype == "success":
        text_style = "✅ "
    elif embedtype == "warning":
        text_style = "⚠️ "
    else:
        text_style = ""

    container.add_item(ui.TextDisplay(label=f"{text_style}{embedtitle}", style="PRIMARY"))
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(label=description, style="SECONDARY"))

    return container

def getguild(id):
    header = {
        "Authorization" : "Bot "
    }
    r = requests.get(f'https://discord.com/api/v9/guilds/{id}',headers=header)
    return r.json()

def start_db():
      con = sqlite3.connect("database.db")
      cur = con.cursor()
      return con, cur

async def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not (await is_guild(id)):
        return False
    con,cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[2]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith(".메시지생성"):
        if message.author.id != owner:
            await message.channel.send("권한이 없습니다.", delete_after=5)
            return

        await message.delete()

        class AuthContainerView(ui.LayoutView):
            def __init__(self):
                super().__init__(timeout=None)
                state = message.guild.id
                redirect_uri = "https://restore.cloud-mkt.xyz/join"
                redirect_uri_encoded = quote(redirect_uri, safe='')
                rd_url = f"https://discord.com/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri_encoded}&response_type=code&scope=identify%20email%20guilds.join&state={state}"
                c = ui.Container()
                c.accent_color = discord.Color.blue()
                c.add_item(ui.TextDisplay("## Cloud Market"))
                c.add_item(ui.Separator())
                c.add_item(ui.TextDisplay(f"Please authorize your account [여기]({rd_url}) to see other channels.\n"
                                          f"다른 채널을 보려면 [여기]({rd_url})를 눌러 계정을 인증해주세요."))
                c.add_item(ui.Separator())

                auth_btn = ui.Button(label="인증하기", url="https://restore.cloud-mkt.xyz/join")
                class InfoButton(ui.Button):
                    def __init__(self):
                        super().__init__(label="수집 정보 보기", style=discord.ButtonStyle.secondary)

                    async def callback(self, interaction: discord.Interaction):
                        c = ui.Container()
                        c.accent_color = discord.Color.green()
                        c.add_item(ui.TextDisplay("## 서버가 수집하는 정보"))
                        c.add_item(ui.Separator())
                        c.add_item(ui.TextDisplay("> 길드정보 :\n- **비활성화**\n"
                                                  "> IP 정보 :\n- **비활성화**\n"
                                                  "> 기기 정보 :\n- **비활성화**\n"
                                                  "이메일 정보 :\n- **비활성화**"))
                        c.add_item(ui.Separator())
                        c.add_item(ui.TextDisplay("- © 2025. Cloud Market. All rights reserved."))

                        v = ui.LayoutView()
                        v.add_item(c)

                        await interaction.response.send_message(view=v,ephemeral=True)

                info_btn = InfoButton()
                c.add_item(ui.ActionRow(auth_btn, info_btn))

                self.add_item(c)

        await message.channel.send(view=AuthContainerView())

    if message.content.startswith(".생성"):
        if message.author.id == owner:
            if not isinstance(message.channel, discord.channel.DMChannel):
                try:
                    amount = int(message.content.split(" ")[1])
                except:
                    await message.channel.send("올바른 생성 갯수를 입력해주세요.")
                    return
                if 1 <= amount <= 30:
                    try:
                        license_length = int(message.content.split(" ")[2])
                    except:
                        await message.channel.send("올바른 생성 기간을 입력해주세요.")
                        return
            con, cur = start_db()
            generated_key = []
            for _ in range(amount):
                key = "CloudMkt-" + randomstring.pick(20)
                generated_key.append(key)
                cur.execute("INSERT INTO licenses VALUES(?, ?);", (key, license_length))
                con.commit()
            con.close()
            c = ui.Container()
            c.accent_color = discord.Color.green()
            c.add_item(ui.TextDisplay("## 생성 성공"))
            c.add_item(ui.Separator())
            c.add_item(ui.TextDisplay("디엠을 확인해주세요."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            await message.author.send("\n".join(generated_key))
        else:
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("## 생성 실패"))
            c.add_item(ui.Separator())
            c.add_item(ui.TextDisplay("권한이 없습니다."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)

    if message.guild is not None and (message.author.id == message.guild.owner_id or message.author.id == owner):
        if message.content.startswith(".등록 "):
            license_number = message.content.split(" ")[1]
            con, cur = start_db()
            cur.execute("SELECT * FROM licenses WHERE key == ?;", (license_number,))
            key_info = cur.fetchone()
            if not key_info:
                con.close()
                c = ui.Container()
                c.accent_color = discord.Color.red()
                c.add_item(ui.TextDisplay("## 오류"))
                c.add_item(ui.Separator())
                c.add_item(ui.TextDisplay("라이센스가 존재하지 않습니다."))
                view = ui.LayoutView()
                view.add_item(c)
                await message.channel.send(view=view)
                return
            cur.execute("DELETE FROM licenses WHERE key == ?;", (license_number,))
            con.commit()
            con.close()
            key_length = key_info[1]

            if await is_guild(message.guild.id):
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                expire_date = guild_info[2]
                new_expiredate = make_expiretime(key_length) if is_expired(expire_date) else add_time(expire_date, key_length)
                cur.execute("UPDATE guilds SET expiredate = ? WHERE id == ?;", (new_expiredate, message.guild.id))
                con.commit()
                con.close()
                c = ui.Container()
                c.accent_color = discord.Color.green()
                c.add_item(ui.TextDisplay("## 등록 성공"))
                c.add_item(ui.Separator())
                c.add_item(ui.TextDisplay(f"기간이 연장되었습니다.\n다음 만료일 : {new_expiredate}"))
                view = ui.LayoutView()
                view.add_item(c)
                await message.channel.send(view=view)
            else:
                try:
                    await register_redirect_url(message.guild.id)
                    con, cur = start_db()
                    new_expiredate = make_expiretime(key_length)
                    recover_key = str(uuid.uuid4())[:8].upper()
                    cur.execute("INSERT INTO guilds VALUES(?, ?, ?, ?);", (message.guild.id, recover_key, new_expiredate, ''))
                    con.commit()
                    con.close()
                    def check(x):
                        return isinstance(x.channel, discord.channel.DMChannel) and x.author.id == message.author.id
                    c = ui.Container()
                    c.add_item(ui.TextDisplay("URL을 입력해주세요. ( /URL < 이부분 )"))
                    view = ui.LayoutView()
                    view.add_item(c)
                    await message.author.send(view=view)
                    c2 = ui.Container()
                    c2.accent_color = discord.Color.green()
                    c2.add_item(ui.TextDisplay("## 안내"))
                    c2.add_item(ui.Separator())
                    c2.add_item(ui.TextDisplay("DM을 확인해 주세요."))
                    view2 = ui.LayoutView()
                    view2.add_item(c2)
                    await message.channel.send(view=view2)
                    x = await client.wait_for("message", timeout=60, check=check)
                    link = x.content
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE link == ?", (link,))
                    find = cur.fetchone()
                    if not find:
                        con = sqlite3.connect("database.db")
                        cur = con.cursor()
                        a = getguild(message.guild.id)
                        cur.execute("UPDATE guilds SET link = ? WHERE id == ?;", (link, message.guild.id))
                        con.commit()
                        con.close()
                        c3 = ui.Container()
                        c3.accent_color = discord.Color.green()
                        c3.add_item(ui.TextDisplay(f"## 등록 완료\n만료일 : {new_expiredate}\n서버링크 : /{link}\n디엠으로 복구키가 전송되었습니다."))
                        view3 = ui.LayoutView()
                        view3.add_item(c3)
                        await message.channel.send(view=view3)
                        c4 = ui.Container()
                        c4.add_item(ui.TextDisplay(f"복구 키 : `{recover_key}`\n복구키를 잘 보관해주세요."))
                        view4 = ui.LayoutView()
                        view4.add_item(c4)
                        await message.author.send(view=view4)
                    else:
                        c5 = ui.Container()
                        c5.add_item(ui.TextDisplay("이미 사용중인 링크입니다.\n.링크 명령어로 다시 등록해 주세요."))
                        view5 = ui.LayoutView()
                        view5.add_item(c5)
                        await message.author.send(view=view5)
                except:
                    c = ui.Container()
                    c.add_item(ui.TextDisplay("디엠을 차단하셨거나, 권한이 부족합니다."))
                    view = ui.LayoutView()
                    view.add_item(c)
                    await message.channel.send(view=view)

    if message.content == ".명령어":
        c = ui.Container()
        c.accent_color = discord.Color.blue()
        c.add_item(ui.TextDisplay("## 명령어 목록"))
        c.add_item(ui.Separator())
        c.add_item(ui.TextDisplay(".생성 (갯수) (몇일) : 라이센스를 생성합니다."))
        c.add_item(ui.TextDisplay(".등록 (코드) : 라이센스를 등록합니다."))
        c.add_item(ui.TextDisplay(".링크 : URL을 수정합니다."))
        c.add_item(ui.TextDisplay(".정보 : 라이센스 기간, 인증 유저 수, 서버 초대URL 표시"))
        c.add_item(ui.TextDisplay(".복구 (복구키) : 유저 복구"))
        c.add_item(ui.TextDisplay(".초대 : 봇 초대 링크"))
        view = ui.LayoutView()
        view.add_item(c)
        await message.channel.send(view=view)

    if message.content == ".초대":
        c = ui.Container()
        c.accent_color = discord.Color.blue()
        c.add_item(ui.TextDisplay("## 봇 초대"))
        c.add_item(ui.Separator())
        c.add_item(ui.TextDisplay("[봇 초대 링크](https://discord.com/api/oauth2/authorize?client_id=941007903035359362&permissions=8&scope=bot)"))
        view = ui.LayoutView()
        view.add_item(c)
        await message.channel.send(view=view)

    if message.content == ".정보":
        if not await is_guild_valid(message.guild.id):
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("라이센스가 유효하지 않습니다."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            return
        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
        guild_info = cur.fetchone()
        con.close()
        con, cur = start_db()
        cur.execute("SELECT * FROM users WHERE guild_id == ?;", (message.guild.id,))
        users = list(set(cur.fetchall()))
        con.close()
        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (message.guild.id,))
        link = cur.fetchone()[3]
        con.close()
        c = ui.Container()
        c.accent_color = discord.Color.green()
        c.add_item(ui.TextDisplay(f"## 서버 정보\n남은 기간 : {get_expiretime(guild_info[2])}\n인증 유저 수 : {len(users)}\n서버 링크 : /{link}"))
        view = ui.LayoutView()
        view.add_item(c)
        await message.channel.send(view=view)

    if message.content.startswith(".복구 "):
        if message.author.id != owner:
            return
        recover_key = message.content.split(" ")[1]
        if await is_guild_valid(message.guild.id):
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("라이센스를 등록하기 전에 복구를 진행해주세요."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            return
        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE token == ?;", (recover_key,))
        token_result = cur.fetchone()
        con.close()
        if not token_result:
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("복구 키가 틀렸습니다."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            return
        if not await is_guild_valid(token_result[0]):
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("복구 키가 만료되었습니다."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            return
        if not (await message.guild.fetch_member(client.user.id)).guild_permissions.administrator:
            c = ui.Container()
            c.accent_color = discord.Color.red()
            c.add_item(ui.TextDisplay("봇에게 관리자 권한이 필요합니다."))
            view = ui.LayoutView()
            view.add_item(c)
            await message.channel.send(view=view)
            return

        con, cur = start_db()
        cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
        users = list(set(cur.fetchall()))
        con.close()
        c = ui.Container()
        c.accent_color = discord.Color.green()
        c.add_item(ui.TextDisplay(f"복구 중입니다. 잠시만 기다려주세요. (예상복구인원 : {len(users)})"))
        view = ui.LayoutView()
        view.add_item(c)
        await message.channel.send(view=view)

        for user in users:
            try:
                refresh_token1 = user[1]
                user_id = user[0]
                new_token = await refresh_token(refresh_token1)
                if new_token:
                    new_refresh = new_token["refresh_token"]
                    new_token = new_token["access_token"]
                    await add_user(new_token, message.guild.id, user_id)
                    con, cur = start_db()
                    cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                    con.commit()
                    con.close()
            except:
                pass

        con, cur = start_db()
        cur.execute("UPDATE users SET guild_id = ? WHERE guild_id == ?;", (message.guild.id, token_result[0]))
        cur.execute("UPDATE guilds SET id = ? WHERE id == ?;", (message.guild.id, token_result[0]))
        con.commit()
        con.close()

        c = ui.Container()
        c.accent_color = discord.Color.green()
        c.add_item(ui.TextDisplay("복구가 정상적으로 완료되었습니다!"))
        view = ui.LayoutView()
        view.add_item(c)
        await message.channel.send(view=view)

@client.event
async def on_ready():
    print(f"Login: {client.user}\nInvite Link: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot")
    while True:
        await client.change_presence(activity=discord.Game(f"링크복구봇 | {len(client.guilds)}서버 사용중"),status=discord.Status.online)
        await asyncio.sleep(5)
        await client.change_presence(activity=discord.Game(f"링크복구봇 | {len(client.guilds)}서버 사용중"),status=discord.Status.online)
        await asyncio.sleep(5)

client.run(BOT_TOKEN)
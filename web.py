import os
import requests
from flask import Flask, request, render_template
import duckdb

app = Flask(__name__)

API_ENDPOINT = 'https://discord.com/api/v9'
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_PATH = '/tmp/database.duckdb'

def start_db():
      con = duckdb.connect(DB_PATH)
      cur = con.cursor()
      return con, cur

def get_user_profile(token):
      header = {"Authorization": f"Bearer {token}"}
      res = requests.get("https://discordapp.com/api/v8/users/@me", headers=header)
      if res.status_code != 200:
          return False
      return res.json()

def getguild(gid):
      header = {"Authorization": f"Bot {BOT_TOKEN}"}
      r = requests.get(f'https://discord.com/api/v9/guilds/{gid}', headers=header)
      return r.json()

def add_user(token, uid, gid):
      try:
          jsonData = {"access_token": token}
          header = {"Authorization": f"Bot {BOT_TOKEN}"}
          res = requests.put(f'{API_ENDPOINT}/guilds/{gid}/members/{uid}', json=jsonData, headers=header)
          return res.json()
      except:
          return False

def exchange_code(code):
      api_endpoint = "https://discord.com/api/v10"
      data = {
          'client_id': CLIENT_ID,
          'client_secret': CLIENT_SECRET,
          'grant_type': 'authorization_code',
          'code': code,
          'redirect_uri': "https://restore.cloud-mkt.xyz/join"
      }
      headers = {'Content-Type': 'application/x-www-form-urlencoded'}
      r = requests.post(f"{api_endpoint}/oauth2/token", data=data, headers=headers)
      return r.json()

def getme(gid):
      header = {"Authorization": f"Bot {BOT_TOKEN}"}
      r = requests.get(f'https://discord.com/api/v9/guilds/{gid}?with_counts=true', headers=header)
      return r.json()

@app.route('/<link>', methods=['GET'])
def joi(link):
      try:
          con, cur = start_db()
          cur.execute("SELECT * FROM guilds WHERE link == ?", (link,))
          row = cur.fetchone()
          if not row:
              return render_template("fail.html")
          gid = row[0]
          con.close()
          ginfo = getguild(gid)
          r = getme(gid)
          return render_template("s.html", link=link, id=gid, info=ginfo, icon=ginfo['icon'], member=r['approximate_member_count'])
      except:
          return render_template("fail.html")

@app.route('/join', methods=['GET'])
def callback():
      code = request.args.get('code')
      state = request.args.get('state')
      result = exchange_code(code)
      data = get_user_profile(result['access_token'])
      add_user(result['access_token'], data['id'], int(state))
      con, cur = start_db()
      cur.execute("INSERT INTO users VALUES(?, ?, ?);", (str(data["id"]), result["refresh_token"], int(state)))
      con.commit()
      con.close()
      try:
          return render_template("success.html")
      except:
          return render_template("fail.html")
from flask import Flask, request, abort
from OwlPub import OwlPub
from RepoHandler import RepoHandler
import hmac
from hashlib import sha1
import json


pub = OwlPub()
Webhook = Flask(__name__)


@Webhook.route("/webhook", methods=["POST"])
@Webhook.route("/webhook/<repo_name>", methods=["POST"])
def webhookHandler(repo_name=None):
    pub.loadConfig()
    if repo_name is None:
        payload = json.loads(request.data)
        repo_config = pub.getRepoConfigByCloneUrl(payload['repository']['clone_url'])
    else:
        repo_config = pub.getRepoConfig(repo_name)

    try:
        repo = RepoHandler(repo_config)
    except Exception:
        return 'wtf'

    if 'secret' in repo_config:
        secret = repo_config['secret']
        signature = request.headers.get('X-Hub-Signature').split('=')[1]
        if type(secret) == unicode:
            secret = secret.encode()
        mac = hmac.new(secret, msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

    if request.headers.get('X-Github-Event') == 'push':
        repo.pull()
        repo.regenerate()
    return "OK"

if __name__ == "__main__":
    Webhook.run(debug=True, port=8000)

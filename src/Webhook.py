from flask import Flask, request, abort
from OwlPub import OwlPub, RepositoryNotFoundError
import hmac
from hashlib import sha1
import json


publisher = OwlPub()
Webhook = Flask(__name__)


def checkSecret(config):
    pass


@Webhook.route("/webhook", methods=["POST"])
def handlerByCloneUrl():
    publisher.loadConfig()
    try:
        payload = json.loads(request.payload)
        clone_url = payload['repository']['clone_url']
        repo = publisher.getRepoByCloneUrl(clone_url)
    except RepositoryNotFoundError, e:
        raise e

    if 'secret' in repo.config:
        secret = repo.config['secret']
        signature = request.headers.get('X-Hub-Signature').split('=')[1]
        if type(secret) == unicode:
            secret = secret.encode()
        mac = hmac.new(secret, msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

    repo.sync()
    repo.regenerate()
    return "OK"


@Webhook.route("/webhook/<webhook_id>", methods=["POST", "GET"])
def handlerByWebhookId(webhook_id):
    publisher.loadConfig()
    try:
        repo = publisher.getRepoByWebhookId(int(webhook_id))
    except RepositoryNotFoundError as e:
        return str(e)

    if 'secret' in repo.config:
        secret = repo.config['secret']
        signature = request.headers.get('X-Hub-Signature').split('=')[1]
        if type(secret) == unicode:
            secret = secret.encode()
        mac = hmac.new(secret, msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

    repo.sync()
    repo.regenerate()
    return "OK"

if __name__ == "__main__":
    Webhook.run(port=8000, debug=True)

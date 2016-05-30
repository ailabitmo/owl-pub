import hmac
import json
from hashlib import sha1

from flask import Flask, request, abort

from OwlPub import OwlPub, RepositoryNotFoundError

publisher = OwlPub()
Webhook = Flask(__name__)


def __check_secret(config):
    signature = request.headers.get('X-Hub-Signature')
    if 'secret' in config and signature:
        secret = config['secret']
        signature = signature.split('=')[1]
        if type(secret) == unicode:
            secret = secret.encode()
        mac = hmac.new(secret, msg=request.data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)


@Webhook.route('/webhook', methods=['POST'])
def handler_by_clone_url():
    try:
        payload = json.loads(request.payload)
        full_name = payload['repository']['full_name']
        repo = publisher.get_repo_by_name(full_name)
    except RepositoryNotFoundError, e:
        raise e

    __check_secret(repo.config)

    repo.sync()
    repo.regenerate()

    return 'OK'


@Webhook.route('/webhook/<webhook_id>', methods=['POST', 'GET'])
def handler_by_webhook_id(webhook_id):
    try:
        repo = publisher.get_repo_by_webhook_id(int(webhook_id))
    except RepositoryNotFoundError as e:
        return str(e)

    __check_secret(repo.config)

    repo.sync()
    repo.regenerate()

    return 'OK'


if __name__ == '__main__':
    Webhook.run(port=8000, debug=True)

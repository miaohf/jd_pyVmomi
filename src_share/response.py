from flask import jsonify


def return_info(code, msg):
    d = {'returnCode': code,
         'returnMsg': msg}
    return jsonify(d)

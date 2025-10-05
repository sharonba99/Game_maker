from flask import jsonify

def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code, msg, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), status

def norm(x):
    return (x or "").strip()

def ensure_answers(arr):
    if not isinstance(arr, list) or len(arr) != 4:
        return False, "answers must be an array of 4 items"
    if any(not norm(a) for a in arr):
        return False, "answers must not contain empty texts"
    return True, None

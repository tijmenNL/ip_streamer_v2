import re

try:
    from flask.json import jsonify
except ImportError:
    from flask.helpers import jsonify

from sipsimple.configuration import DefaultValue

__all__ = ['error_response', 'get_json', 'get_state', 'jsonify', 'set_state']


class SettingsParser(object):

    @classmethod
    def parse(cls, type, value):
        if value == 'None':
            return None
        if value == 'DEFAULT':
            return DefaultValue
        parser = getattr(cls, 'parse_%s' % type.__name__, cls.parse_default)
        return parser(type, value)


def get_state(obj):
    def cleanup_state(o, old_state):
        state = {}
        for k, v in old_state.iteritems():
            if v is DefaultValue:
                v = getattr(o, k)
            elif isinstance(v, dict):
                v = cleanup_state(getattr(o, k), v)
            if hasattr(v, '__getstate__'):
                v = v.__getstate__()
            if v in ('true', 'false'):
                # fix booleans to be real booleans and not strings
                v = True if v=='true' else False
            state[k] = v
        return state
    return cleanup_state(obj, obj.__getstate__())


def set_state(obj, state):
    for k, v in state.iteritems():
        if isinstance(v, dict):
            o = getattr(obj, k, None)
            set_state(o, v)
        elif obj is not None:
            name = k
            value = v
            try:
                attribute = getattr(type(obj), name)
                value = SettingsParser.parse(attribute.type, value)
                setattr(obj, name, value)
            except AttributeError:
                raise ValueError('Unknown setting: %s' % name)
            except ValueError, e:
                raise ValueError('%s: %s' % (name, str(e)))


def error_response(code, reason='unkwnown'):
    return jsonify({'msg': reason}), code


def get_json(request):
    try:
        return request.get_json(silent=True)
    except AttributeError:
        try:
            return request.json
        except Exception:
            return None

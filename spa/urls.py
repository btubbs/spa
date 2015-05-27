from werkzeug.routing import Map, Rule


def build_rules(rules_tuples):
    handlers = {}
    rules = []
    for pat, name, handler, kwargs in [tuple_to_rule(t) for t in rules_tuples]:
        rules.append(Rule(pat, endpoint=name))
        handlers[name] = handler, kwargs
    return Map(rules), handlers


def tuple_to_rule(tpl):
    pat, name, handler = tpl[0], tpl[1], tpl[2]
    if len(tpl) > 3:
        kwargs = tpl[3]
    else:
        kwargs = {}
    return pat, name, handler, kwargs


def reverse(rule_map, endpoint, values=None):
    """ Given a rule map, and the name of one of our endpoints, and a dict of
    parameter values, return a URL"""
    adapter = rule_map.bind('')
    return adapter.build(endpoint, values=values)

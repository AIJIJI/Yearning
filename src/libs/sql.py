import re

def parse(sql: StopIteration) -> bool:
    for i in sql.split():
        for c in ['update', 'insert', 'alter', 'into', 'for', 'drop']:
            if i == c:
                return True
    return False


def as_ex(sql, sensitive_list):
    count = 0
    sentences = sql.split(',')
    complete = []
    for sentence in sentences:
        words = sentence.split(' ')
        for word in words:
            if word != '':
                complete.append(word)
    for gen in complete:
        if gen == 'as':
            count += 1
    if not count:
        return sensitive_list
    as_list = []
    for i, _ in enumerate(complete):
        if complete[i] == 'as':
            for s in sensitive_list:
                if complete[i - 1] == s:
                    as_list.append(complete[i + 1].rstrip(','))

    if as_list is not None:
        for sen_i in as_list:
            sensitive_list.append(sen_i)
    return sensitive_list


def replace_limit(sql, limit):
    '''

    :argument 根据正则匹配分析输入信息 当limit数目超过配置文件规定的最大数目时将会采用配置文件的最大数目

    '''
    if sql[-1] != ';':
        sql += ';'
    sql_re = re.search(r'limit\s.*\d.*;', sql.lower())
    length = ''
    if sql_re:
        c = re.search(r'\d.*', sql_re.group())
        if c:
            if c.group().find(',') != -1:
                length = c.group()[-2]
            else:
                length = c.group().rstrip(';')
        if int(length) <= int(limit):
            return sql
        else:
            return re.sub(r'limit\s.*\d.*;', 'limit %s;' % limit, sql)
    else:
        return sql.rstrip(';') + ' limit %s;' % limit

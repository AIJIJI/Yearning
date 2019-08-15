import ast
import math
import datetime
import json
from decimal import Decimal

import simplejson
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from core.models import DatabaseList, globalpermissions, QueryHistory
from core.task import set_auth_group
from libs import con_database, util
from libs.serializers import QueryHistorySerializers
import libs

def exclued_db_list():
    try:
        setting = globalpermissions.objects.filter(
            authorization='global').first()
        exclued_database_name = setting.other.get('exclued_db_list', [])
    except Exception:
        exclued_database_name = []
    return exclued_database_name


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def databases(request):
    tablelist = []
    highlist = []
    connection_name = request.GET['connection']
    _connection = DatabaseList.objects.filter(
        connection_name=connection_name).first()
    with con_database.SQLgo(ip=_connection.ip,
                            user=_connection.username,
                            password=_connection.password,
                            port=_connection.port) as f:
        print('连接成功')
        databases = f.query_info(sql='show databases')
    ignore = exclued_db_list()
    for index, uc in sorted(enumerate(databases), reverse=True):
        for cc in ignore:
            if uc['Database'] == cc:
                del databases[index]
    for i in databases:
        highlist.append({'vl': i['Database'], 'meta': '库名'})
        tablelist.append({
            'title': i['Database'],
            'children': [{}]
        })
    data = [{
        'title': connection_name,
        'expand': 'true',
        'children': tablelist
    }]
    return JsonResponse({'info': data, 'highlight': highlist})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def table(request):
    permission_spec = set_auth_group(request.user)
    if request.GET['connection'] not in permission_spec['querycon']:
        return HttpResponse('非法请求,账号无查询权限！')
    connection = DatabaseList.objects\
        .filter(connection_name=request.GET['connection'])\
        .first()
    with con_database.SQLgo(
            ip=connection.ip,
            user=connection.username,
            password=connection.password,
            port=connection.port,
            db=request.GET['database']) as f:
        # data_set = f.search(sql='desc %s' % request.GET['table'])
        field = f.gen_alter(table_name=request.GET['table'])
        idx = f.index(table_name=request.GET['table'])
        return JsonResponse({'idx': idx, 'field': field})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tables(request):
    permission_spec = set_auth_group(request.user)
    if request.GET['connection'] not in permission_spec['querycon']:
        return HttpResponse('非法请求,账号无查询权限！')
    highlist = []
    children = []
    connection = DatabaseList.objects\
        .filter(connection_name=request.GET['connection'])\
        .first()
    with con_database.SQLgo(ip=connection.ip,
                            user=connection.username,
                            password=connection.password,
                            port=connection.port,
                            db=request.GET['database']) as f:
        tablename = f.query_info(sql='show tables')
        for c in tablename:
            key = 'Tables_in_%s' % request.GET['database']
            field = f.query_info(
                sql='select COLUMN_NAME from information_schema.COLUMNS where table_name = "%s"' % c[key])
            for z in field:
                highlist.append(
                    {'vl': z['COLUMN_NAME'], 'meta': '字段名'})
            highlist.append({'vl': c[key], 'meta': '表名'})
            children.append({
                'title': c[key]
            })
    return JsonResponse({'table': children, 'highlight': highlist})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    if int(request.GET.get('all', '0')):
        historys = QueryHistory.objects.all()
        username = request.GET.get('user')
        if username:
            historys = historys.filter(user__username__icontains=username)
        start, end = request.GET.getlist('pickers')
        if start and end:
            historys = historys.filter(date__gte=start, date__lte=end)
        page = request.GET.get('page')
        end = int(page) * 20
        start = end - 20
        total = historys.count()
        return JsonResponse({
            'data': QueryHistorySerializers(historys[start:end], many=True).data,
            'total': total
        })
    else:
        database = request.GET['database']
        connection = DatabaseList.objects.filter(connection_name=request.GET['connection']).first()
        historys = QueryHistory.objects.filter(
            connection=connection,
            database=database,
            user=request.user)
        return JsonResponse(QueryHistorySerializers(historys, many=True).data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sql(request):
    un_init = util.init_conf()
    limit = ast.literal_eval(un_init['other'])
    sql = request.data['sql']
    check = str(sql).lower().strip().split(';\n')
    raw_sql = str(sql).strip().split(';\n')[-1]
    un_init = util.init_conf()
    custom_com = ast.literal_eval(un_init['other'])
    critical = len(custom_com['sensitive_list'])
    permission_spec = set_auth_group(request.user)
    if request.data['connection'] not in permission_spec['querycon']:
        return HttpResponse('非法请求,账号无查询权限！')
    if not check[-1].startswith('s'):
        return HttpResponse('请勿使用非查询语句,请删除不必要的空白行！')
    _c = DatabaseList.objects.filter(
        computer_room=request.data['cabinet'],
        connection_name=request.data['connection'],
    ).first()
    with con_database.SQLgo(
            ip=_c.ip,
            password=_c.password,
            user=_c.username,
            port=_c.port,
            db=request.data['database']
    ) as f:
        try:
            if libs.sql.parse(check[-1]):
                return HttpResponse('语句中不得含有违禁关键字: update insert alter into for drop')

            query_sql = raw_sql
            if not check[-1].startswith('show') and int(request.GET.get('with_limit', '0')):
                if limit.get('limit').strip() == '':
                    query_sql = libs.sql.replace_limit(raw_sql, 1000)
                else:
                    query_sql = libs.sql.replace_limit(
                        raw_sql, limit.get('limit'))
            data_set = f.search(sql=query_sql)
            if int(request.GET.get('log', '0')):
                log = QueryHistory(
                    user=request.user,
                    sql=query_sql,
                    date=datetime.datetime.now(),
                    count=len(data_set['data']),
                    connection=_c,
                    database=request.data['database']
                    )
                log.save()
        except Exception as e:
            return HttpResponse(e)
        else:
            if critical:
                as_list = libs.sql.as_ex(
                    sql, custom_com['sensitive_list'])
                if data_set['data']:
                    fe = []
                    for k, v in data_set['data'][0].items():
                        if isinstance(v, bytes):
                            fe.append(k)
                    for l in data_set['data']:
                        for i in fe:
                            l[i] = 'blob字段为不可呈现类型'
                        for s in as_list:
                            l[s] = '********'
            elif data_set['data']:
                fe = []
                for k, v in data_set['data'][0].items():
                    if isinstance(v, bytes):
                        fe.append(k)
                for i in fe:
                    for l in data_set['data']:
                        l[i] = 'blob字段为不可呈现类型'

        return JsonResponse(data_set, encoder=ResultEncoder)


class ResultEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time, datetime.timedelta)):
            return str(o)
        if isinstance(o, int):
            return str(o)
        if isinstance(o, Decimal):
            return str(o)
        return simplejson.JSONEncoder.default(self, o)

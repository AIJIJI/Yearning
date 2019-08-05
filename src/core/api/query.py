import ast
import datetime
import json

import simplejson
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.models import DatabaseList, querypermissions, query_order, globalpermissions
from core.task import set_auth_group
from libs import con_database, util
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
    # connection_name = request.GET['connection']
    # database_name = request.GET['database']
    # highlist = []
    # children = []
    # _connection = DatabaseList.objects.filter(
    #     connection_name=connection_name).first()
    # with con_database.SQLgo(ip=_connection.ip,
    #                         user=_connection.username,
    #                         password=_connection.password,
    #                         port=_connection.port,
    #                         db=database_name) as f:
    #     tablename = f.query_info(sql='show tables')
    #     for c in tablename:
    #         key = 'Tables_in_%s' % database_name
    #         field = f.query_info(
    #             sql='select COLUMN_NAME from information_schema.COLUMNS where table_name = "%s"' % c[key])
    #         for z in field:
    #             highlist.append(
    #                 {'vl': z['COLUMN_NAME'], 'meta': '字段名'})
    #         highlist.append({'vl': c[key], 'meta': '表名'})
    #         children.append({
    #             'title': c[key]
    #         })
    # return JsonResponse({'table': children, 'highlight': highlist})
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
        return JsonResponse({ 'idx': idx, 'field': field })

# class DirectQuery(baseview.BaseView):

#     def get(self, request, args: str = None):
#         page = request.GET.get('page')
#         query = json.loads(request.GET.get('query'))
#         end = int(page) * 20
#         start = end - 20
#         if query['valve']:
#             if query['picker'][0] == '':
#                 info = query_order.objects\
#                     .filter(username__contains=query['user'])\
#                     .order_by('-id')[start:end]
#                 page_number = query_order.objects\
#                     .filter(username__contains=query['user'])\
#                     .only('id').count()
#             else:
#                 picker = []
#                 for i in query['picker']:
#                     picker.append(i)
#                 info = query_order.objects\
#                     .filter(username__contains=query['user'],
#                             date__gte=picker[0],
#                             date__lte=picker[1])\
#                     .order_by('-id')[start:end]
#                 page_number = query_order.objects\
#                     .filter(username__contains=query['user'], date__gte=picker[0],
#                             date__lte=picker[1])\
#                     .only('id').count()
#         else:
#             info = query_order.objects.all().order_by('-id')[start:end]
#             page_number = query_order.objects.only('id').count()
#         serializers = Query_review(info, many=True)
#         return Response({'page': page_number, 'data': serializers.data})

#     def post(self, request, args: str = None):

#         work_id = request.data['workid']
#         user = request.data['user']
#         data = querypermissions.objects.filter(
#             work_id=work_id, username=user).all().order_by('-id')
#         serializers = Query_list(data, many=True)
#         return Response(serializers.data)

#     def put(self, request, args: str = None):

#         if request.data['mode'] == 'put':
#             instructions = request.data['instructions']
#             connection_name = request.data['connection_name']
#             computer_room = request.data['computer_room']
#             real = request.data['real_name']
#             export = request.data['export']
#             audit = request.data['audit']
#             un_init = util.init_conf()
#             query_switch = ast.literal_eval(un_init['other'])
#             query_per = 2
#             work_id = util.workId()
#             if not query_switch['query']:
#                 query_per = 2
#             else:
#                 userinfo = Account.objects.filter(
#                     username=audit, group='admin').first()
#                 try:
#                     thread = threading.Thread(
#                         target=push_message,
#                         args=(
#                             {'to_user': request.user,
#                                 'workid': work_id}, 5, request.user, userinfo.email, work_id,
#                             '提交'))
#                     thread.start()
#                 except Exception as e:
#                     CUSTOM_ERROR.error(f'{e.__class__.__name__}: {e}')
#             query_order.objects.create(
#                 work_id=work_id,
#                 instructions=instructions,
#                 username=request.user,
#                 date=util.date(),
#                 query_per=query_per,
#                 connection_name=connection_name,
#                 computer_room=computer_room,
#                 export=export,
#                 audit=audit,
#                 time=util.date(),
#                 real_name=real
#             )
#             if not query_switch['query']:
#                 query_order.objects.filter(work_id=work_id).update(query_per=1)
#             # 钉钉及email站内信推送
#             return Response('查询工单已提交，等待管理员审核！')

#         elif request.data['mode'] == 'agree':
#             work_id = request.data['work_id']
#             query_info = query_order.objects.filter(
#                 work_id=work_id).order_by('-id').first()
#             query_order.objects.filter(work_id=work_id).update(query_per=1)
#             userinfo = Account.objects.filter(
#                 username=query_info.username).first()
#             try:
#                 thread = threading.Thread(target=push_message, args=(
#                     {'to_user': query_info.username,
#                      'workid': query_info.work_id}, 6, query_info.username,
#                     userinfo.email,
#                     work_id, '同意'))
#                 thread.start()
#             except Exception as e:
#                 CUSTOM_ERROR.error(f'{e.__class__.__name__}: {e}')
#             return Response('查询工单状态已更新！')

#         elif request.data['mode'] == 'disagree':
#             work_id = request.data['work_id']
#             query_order.objects.filter(work_id=work_id).update(query_per=0)
#             query_info = query_order.objects.filter(
#                 work_id=work_id).order_by('-id').first()
#             userinfo = Account.objects.filter(
#                 username=query_info.username).first()
#             try:
#                 thread = threading.Thread(target=push_message, args=(
#                     {'to_user': query_info.username,
#                      'workid': query_info.work_id}, 7, query_info.username,
#                     userinfo.email,
#                     work_id, '驳回'))
#                 thread.start()
#             except Exception as e:
#                 CUSTOM_ERROR.error(f'{e.__class__.__name__}: {e}')
#             return Response('查询工单状态已更新！')

#         elif request.data['mode'] == 'status':
#             try:
#                 status = query_order.objects.filter(
#                     username=request.user).order_by('-id').first()
#                 return Response(status.query_per)
#             except Exception as e:
#                 CUSTOM_ERROR.error(f'{e.__class__.__name__}: {e}')
#                 return Response(0)

#         elif request.data['mode'] == 'end':
#             try:
#                 query_order.objects.filter(username=request.data['username']).order_by(
#                     '-id').update(query_per=3)
#                 return Response('已结束查询！')
#             except Exception as e:
#                 return HttpResponse(e)

#         elif request.data['mode'] == 'info':
#             tablelist = []
#             highlist = []
#             database = query_order.objects.filter(
#                 username=request.user).order_by('-id').first()
#             _connection = DatabaseList.objects.filter(
#                 connection_name=database.connection_name).first()
#             with con_database.SQLgo(ip=_connection.ip,
#                                     user=_connection.username,
#                                     password=_connection.password,
#                                     port=_connection.port) as f:
#                 dataname = f.query_info(sql='show databases')
#             ignore = exclued_db_list()
#             for index, uc in sorted(enumerate(dataname), reverse=True):
#                 for cc in ignore:
#                     if uc['Database'] == cc:
#                         del dataname[index]
#             for i in dataname:
#                 highlist.append({'vl': i['Database'], 'meta': '库名'})
#                 tablelist.append({
#                     'title': i['Database'],
#                     'children': [{}]
#                 })
#             data = [{
#                 'title': database.connection_name,
#                 'expand': 'true',
#                 'children': tablelist
#             }]
#             return Response({'info': json.dumps(data), 'status': database.export, 'highlight': highlist})

#         elif request.data['mode'] == 'table':
#             basename = request.data['base']
#             highlist = []
#             children = []
#             database = query_order.objects.filter(
#                 username=request.user).order_by('-id').first()
#             _connection = DatabaseList.objects.filter(
#                 connection_name=database.connection_name).first()
#             with con_database.SQLgo(ip=_connection.ip,
#                                     user=_connection.username,
#                                     password=_connection.password,
#                                     port=_connection.port,
#                                     db=basename) as f:
#                 tablename = f.query_info(sql='show tables')
#                 for c in tablename:
#                     key = 'Tables_in_%s' % basename
#                     field = f.query_info(
#                         sql='select COLUMN_NAME from information_schema.COLUMNS where table_name = "%s"' % c[key])
#                     for z in field:
#                         highlist.append(
#                             {'vl': z['COLUMN_NAME'], 'meta': '字段名'})
#                     highlist.append({'vl': c[key], 'meta': '表名'})
#                     children.append({
#                         'title': c[key]
#                     })
#             return Response({'table': children, 'highlight': highlist})

#     def delete(self, request, args: str = None):
#         data = query_order.objects.filter(
#             username=request.user).order_by('-id').first()
#         query_order.objects.filter(work_id=data.work_id).delete()
#         return Response('')


class SQL(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        un_init = util.init_conf()
        limit = ast.literal_eval(un_init['other'])
        sql = request.data['sql']
        check = str(sql).lower().strip().split(';\n')
        raw_sql = str(sql).strip().split(';\n')[-1]
        user = query_order.objects.filter(
            username=request.user).order_by('-id').first()
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
                if not check[-1].startswith('show') and int(request.data.get('with_limit', '0')):
                    if limit.get('limit').strip() == '':
                        query_sql = libs.sql.replace_limit(raw_sql, 1000)
                    else:
                        query_sql = libs.sql.replace_limit(
                            raw_sql, limit.get('limit'))
                data_set = f.search(sql=query_sql)
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

                querypermissions.objects.create(
                    work_id=user.work_id,
                    username=request.user,
                    statements=query_sql
                )
            return JsonResponse(data_set, encoder=ResultEncoder)


class ResultEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time, datetime.timedelta)):
            return str(o)
        if isinstance(o, int):
            return str(o)
        return simplejson.JSONEncoder.default(self, o)

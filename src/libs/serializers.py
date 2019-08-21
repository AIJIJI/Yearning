'''
serializers 
'''
from rest_framework import serializers
from core import models
from core.models import DatabaseList
from core.models import SqlRecord
from core.models import Account
from core.models import SqlOrder, query_order, globalpermissions, grained


class Globalpermissions(serializers.HyperlinkedModelSerializer):
    '''
    站内信列表serializers
    '''

    class Meta:
        model = globalpermissions
        fields = ('inception', 'ldap', 'other', 'message')


class UserINFO(serializers.HyperlinkedModelSerializer):
    '''
    平台用户信息列表serializers
    '''

    class Meta:
        model = Account
        fields = ('id', 'username', 'group', 'department', 'email', 'auth_group', 'real_name')


class Sqllist(serializers.HyperlinkedModelSerializer):
    '''
    数据库连接信息serializers
    '''

    class Meta:
        model = DatabaseList
        fields = ('id', 'connection_name', 'ip', 'computer_room', 'password', 'port', 'username', 'before', 'after')


class query_con(serializers.HyperlinkedModelSerializer):
    '''
    查询连接信息serializers
    '''

    class Meta:
        model = DatabaseList
        fields = ('connection_name', 'computer_room')


class Area(serializers.HyperlinkedModelSerializer):
    '''
    SQL提交及表结构修改页面数据库连接信息返回serializers
    '''

    class Meta:
        model = DatabaseList
        fields = ('id', 'connection_name', 'ip', 'computer_room')


class Record(serializers.HyperlinkedModelSerializer):
    '''
    执行工单的详细信息serializers
    '''

    class Meta:
        model = SqlRecord
        fields = ('sql', 'state', 'error', 'affectrow', 'sequence', 'execute_time')


class RecordSerializer(serializers.ModelSerializer):

    connection_name = serializers.SlugRelatedField(
        source='bundle',
        read_only=True, slug_field='connection_name'
    )

    computer_room = serializers.SlugRelatedField(
        source='bundle',
        read_only=True, slug_field='computer_room'
    )

    class Meta:
        model = SqlOrder
        fields = '__all__'


class Query_review(serializers.HyperlinkedModelSerializer):
    '''

    查询审计

    '''

    class Meta:
        model = query_order
        fields = (
            'work_id', 'username', 'date', 'instructions', 'query_per', 'connection_name', 'computer_room',
            'export', 'time', 'real_name')


# class Query_list(serializers.HyperlinkedModelSerializer):
#     '''

#     查询审计

#     '''

#     class Meta:
#         model = querypermissions
#         fields = ('id', 'statements')


class AuthGroup_Serializers(serializers.HyperlinkedModelSerializer):
    """
    序列化权限组
    """

    class Meta:
        model = grained
        fields = ('id', 'username', 'permissions',)


class QueryHistorySerializers(serializers.ModelSerializer):

    connection = query_con(read_only=True)
    user = UserINFO(read_only=True)
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    
    class Meta:
        model = models.QueryHistory
        fields = '__all__'

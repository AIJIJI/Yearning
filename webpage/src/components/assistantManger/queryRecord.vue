<style lang="less">
@import "../../styles/common.less";
@import "../order/components/table.less";
</style>
<template>
  <div>
    <Row>
      <Card>
        <p slot="title">
          <Icon type="md-person"></Icon>查询审计
        </p>
        <Row>
          <i-col span="24">
            <Form inline>
              <FormItem>
                <Input placeholder="账号名" v-model="find.user"></Input>
              </FormItem>
              <FormItem>
                <DatePicker format="yyyy-MM-dd HH:mm" type="datetimerange" placeholder="请选择查询的时间范围"
                            v-model="find.picker" @on-change="find.picker=$event" style="width: 250px" :editable="false"></DatePicker>
              </FormItem>
              <FormItem>
                <Button type="success" @click="queryData">查询</Button>
                <Button type="primary" @click="queryCancel">重置</Button>
              </FormItem>
            </Form>
            <Table border :columns="columns" :data="table_data" stripe size="small" height="500"></Table>
          </i-col>
        </Row>
        <br>
        <Page :total="total" show-elevator @on-change="currentpage" :page-size="20"></Page>
      </Card>
    </Row>
  </div>
</template>
<script>
import axios from 'axios';

export default {
  name: 'put',
  data () {
    return {
      columns: [
        { title: '下载时间', key: 'date', sortable: true, width: 131 },
        { title: '连接名', key: 'connection_name', sortable: true, width: 95 },
        { title: '数据库', key: 'database', sortable: true, width: 95 },
        { title: '查询人', key: 'username', width: 95 },
        {
          title: 'SQL',
          key: 'sql'
        }
      ],
      total: 0,
      computer_room: this.$config.computer_room,
      table_data: [],
      find: {
        picker: [],
        user: '',
        valve: false
      }
    };
  },
  methods: {
    currentpage (vl = 1) {
      let url = `${this.$config.url}/query/history?all=1&page=${vl}`
      if (this.find.picker.length === 2) {
        url += `&pickers=${this.find.picker[0]}&pickers=${this.find.picker[1]}`
      }
      if (this.find.user) {
        url += `&user=${this.find.user}`
      }

      axios.get(url).then(res => {
        this.total = res.data.total
        this.table_data = res.data.data.map(item => ({
          ...item,
          connection_name: item.connection.connection_name,
          username: item.user.username,
          realname: item.user.real_name
          }))
      })
      .catch(error => {
        this.$config.err_notice(this, error);
      });
    },
    queryData () {
      this.find.valve = true
      this.currentpage()
    },
    queryCancel () {
      this.find = this.$config.clearPicker(this.find)
      this.currentpage()
    }
  },
  mounted () {
    this.currentpage();
  }
};
</script>

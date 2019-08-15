<style lang="less">
  @import "../../styles/common.less";
  @import "../order/components/table.less";
</style>

<template><div><Row justify="end" >
<i-col v-show="!hideMenuText" :span="hideMenuText ? 0 : 6">
  <Card >
    <div class="edittable-test-con">
      <div id="showImage" class="margin-bottom-10">
        <Form ref="input" :model="input" :label-width="80">
          <FormItem label="机房:" prop="cabinet">
            <Select v-model="input.cabinet" @on-change="ScreenConnection">
              <Option v-for="i in responses.cabinets" :key="i" :value="i">{{i}}</Option>
            </Select>
          </FormItem>
          <FormItem label="连接名:" prop="connection">
            <Select v-model="input.connection" @on-change="onChangeConnection">
              <Option
                v-for="connection in responses.optional_connections"
                :value="connection.name"
                :key="connection.name"
              >{{ connection.connection_name }}
              </Option>
            </Select>
          </FormItem>
        </Form>
      </div>
      <div class="edittable-test-con">
        <div id="showImage" class="margin-bottom-10">
            <div class="tree">
              <Tree
                :data="table_tree"
                @on-select-change="onSelectTree"
                @on-toggle-expand="onExpandTree"
                @empty-text="数据加载中"
              ></Tree>
            </div>
          </div>
      </div>
    </div>
  </Card>
</i-col>
<i-col :span="hideMenuText ? 24 : 18" class="padding-left-10">
  <Card>
    <div slot="title">
      <Button
        type="text"
        @click="onClickHidenMenu"
      >
        <Icon v-if="hideMenuText" type="ios-arrow-forward" />
        <Icon v-else type="ios-arrow-back" />
      </Button>
      <Icon type="ios-crop-strong" />
      <b>填写sql语句</b>
    </div>
    <editor
      ref="editor"
      v-model="input.sql"
      @init="editorInit"
      @setCompletions="setCompletions"
    />
    <br>
    <div v-if="input.table">
      <p>当前选择的表: {{input.database}}.{{input.table}} </p>
    </div>
    <div v-else>
      <p>当前选择的库: {{input.database}}</p></div>
    <br>
    <Button type="error" icon="md-trash" @click.native="ClearForm()">清除</Button>
    <Button type="info" icon="md-brush" @click.native="beautify()">美化</Button>
    <Button
      type="success"
      icon="ios-redo"
      @click.native="onQuerySql()"
      v-if="input.sql && input.cabinet && input.connection"
    >
      <nobr v-if="this.$refs.editor.editor.getCopyText()">
        查询选中语句
      </nobr>
      <nobr v-else>
        查询全部语句
      </nobr>
    </Button>
    <Button
      type="primary"
      icon="ios-cloud-download"
      @click.native="exportdata()"
      v-if="input.sql && input.cabinet && input.connection"
    >查询全部语句并导出数据</Button>
    <br>
    <br>
     <div class="edittable-table-height-con">
      <Tabs>
        <TabPane label="查询结果" name="order1" icon="md-code">
          <Table
            :columns="columnsName"
            :data="query_results_current_page"
            height="500"
            highlight-row
            ref="table"
          />
        </TabPane>
        <TabPane label="表结构详情" name="fields_table" icon="md-folder">
          <Table :columns="fieldColumns" :data="responses.fields" height="500" />
        </TabPane>
        <TabPane label="索引详情" name="indexs_table" icon="md-folder">
          <Table :columns="idxColums" :data="responses.indexs" height="500" />
        </TabPane>
        <TabPane label="下载历史" name="history_table" icon="md-folder">
          <Table :columns="historyColumns" :data="responses.history" height="500" />
        </TabPane>
      </Tabs>
    </div>
    <Page :total="total" show-total @on-change="splice_arr" ref="totol"></Page>
  </Card>
</i-col>
</Row></div></template>

<script>
import Vue from 'vue'
import axios from 'axios'
import Csv from '../../../node_modules/iview/src/utils/csv'
import ExportCsv from '../../../node_modules/iview/src/components/table/export-csv'
import { DEFAULT_COMPUTER_ROOM } from '../../constants'
const concat_ = function (arr1, arr2) {
  let arr = arr1.concat();
  for (let i = 0; i < arr2.length; i++) {
    arr.indexOf(arr2[i]) === -1 ? arr.push(arr2[i]) : 0;
  }
  return arr;
}
function exportcsv (params) {
  if (params.filename) {
    if (params.filename.indexOf('.csv') === -1) {
      params.filename += '.csv'
    }
  } else {
    params.filename = 'table.csv'
  }

  let columns = []
  let datas = []
  if (params.columns && params.data) {
    columns = params.columns
    datas = params.data
  } else {
    columns = this.columns
    if (!('original' in params)) params.original = true
    datas = params.original ? this.data : this.rebuildData
  }

  let noHeader = false
  if ('noHeader' in params) noHeader = params.noHeader
  const data = Csv(columns, datas, params, noHeader)
  if (params.callback) {
    params.callback(data)
  } else {
    ExportCsv.download(params.filename, data)
  }
}
export default {
  components: {
    editor: require('../../libs/editor')
  },
  name: 'DirectQuery',
  data () {
    return {
      hideMenuText: false, // 隐藏左侧数据库选择
      table_tree: [], // 左侧数据库展示树
      total: 0, // 查询结果条目
      invalidDate: {
        disabledDate (date) {
          return date && date.valueOf() < Date.now() - 86400000
        }
      },
      validate_gen: true,
      input: { // 用户交互
        sql: '',  // 输入的 SQL 语句
        cabinet: DEFAULT_COMPUTER_ROOM,  // 机房选择
        connection: '',  // 连接名选择
        database: '', // 用户选择的数据库名
        table: '' // 用户选择的表名
      },
      columnsName: [], // 查询结果列名
      query_results_current_page: [],
      allowed_connections: [], // as IConnection[], // 用户允许访问的连接
      current_connection: {}, // as IConnection, // 当前选中的连接
      responses: {
        optional_connections: [], // as IConnection[] // 下拉菜单中的连接
        basenamelist: [],
        sqllist: [],
        cabinets: [],
        query_results: [], // 查询结果
        fields: [], // 字段信息
        indexs: [], // 索引信息
        history: [] // 下载历史
      },
      id: null,
      wordList: [],
      loading: false,
      fieldColumns: [
        {
          title: '字段名',
          key: 'Field'
        },
        {
          title: '字段类型',
          key: 'Type',
          editable: true
        },
        {
          title: '字段是否为空',
          key: 'Null',
          editable: true,
          option: true
        },
        {
          title: '默认值',
          key: 'Default',
          editable: true
        },
        {
          title: '备注',
          key: 'Extra'
        }
      ],
      idxColums: [
        {
          title: '索引名称',
          key: 'key_name'
        },
        {
          title: '是否唯一索引',
          key: 'Non_unique'
        },
        {
          title: '字段名',
          key: 'column_name'
        }
      ],
      historyColumns: [
        {
          title: '时间',
          key: 'date'
        },
        {
          title: 'SQL',
          key: 'sql'
        },
        {
          title: '结果数',
          key: 'count'
        }
      ]
    }
  },
  methods: {
    setCompletions (editor, session, pos, prefix, callback) {
      callback(null, this.wordList.map(function (word) {
        return {
          caption: word.vl,
          value: word.vl,
          meta: word.meta
        }
      }))
    },

    editorInit: function () {
      require('brace/mode/mysql')
      require('brace/theme/xcode')
    },

    onChangeDatabase (node) {
       this.input.database = node.title
       this.input.table = ''
       axios.get(`${this.$config.url}/query/history?connection=${this.input.connection}&database=${this.input.database}`)
        .then(res => {
          if (res.data['error']) {
            this.$config.err_notice(this, res.data['error'])
          } else {
            this.responses.history = res.data
          }
        })
    },

    onExpandTree (vl) {
      if (vl.expand === true) {
        this.onChangeDatabase(vl)
        axios.get(`${this.$config.url}/query/tables?connection=${this.input.connection}&database=${this.input.database}`)
        .then(res => {
          this.wordList = concat_(this.wordList, res.data.highlight)
          for (let i = 0; i < this.table_tree[0].children.length; i++) {
            if (this.table_tree[0].children[i].title === vl.title) {
              this.table_tree[0].children[i].children = res.data.table
            }
          }
        })
      }
    },

    splice_arr (page) {
      this.query_results_current_page = this.responses.query_results.slice(page * 10 - 10, page * 10)
    },

    beautify () {
      axios.put(`${this.$config.url}/sqlsyntax/beautify`, {
        'data': this.input.sql
      })
        .then(res => {
          this.input.sql = res.data
        })
        .catch(error => {
          this.$config.err_notice(this, error)
        })
    },

    ScreenConnection (cabinet) {
      this.input.connection = ''
      this.responses.optional_connections = this.allowed_connections.filter(
        connection => connection.cabinet === cabinet)
    },

    onChangeConnection (name) {
      // 修改 tag 带连接后缀
      this.$store.state.pageOpenedList.forEach((tag, index) => {
        if (tag.window === this.$store.state.currentPageWindow && tag.name === this.$store.state.currentPageName) {
          Vue.set(this.$store.state.pageOpenedList, index, {...tag, connection: name})
        }
      });
      this.current_connection = this.allowed_connections.filter(
        connection => connection.name === name)
      this.get_databases()
    },

    onClickHidenMenu () {
      this.hideMenuText = !this.hideMenuText
    },

    onQuerySql (isExport = false) {
      this.$Spin.show({
        render: (h) => {
          return h('div', [
            h('Icon', {
              props: {
                size: 30,
                type: 'ios-loading'
              },
              style: {
                animation: 'ani-demo-spin 1s linear infinite'
              }
            }),
            h('div', '正在查询,请稍后........')
          ])
        }
      })
      const selectedText = this.$refs.editor.editor.getCopyText()
      let url = `${this.$config.url}/query/sql/`
      if (isExport) {
        url += '?log=1'
      } else {
        url += '?with_limit=1'
      }
      axios.post(url, {
        'sql': selectedText || this.input.sql,
        'cabinet': this.input.cabinet,
        'connection': this.input.connection,
        'database': this.input.database
      }).then(res => {
        if (!res.data['data']) {
          this.$config.err_notice(this, res.data)
        } else {
          if (isExport) {
            exportcsv({
              filename: 'Yearning_Data',
              original: true,
              data: res.data.data,
              columns: res.data['title']
            })
          } else {
            this.columnsName = res.data['title']
            this.responses.query_results = res.data.data
            this.query_results_current_page = this.responses.query_results.slice(0, 10)
            this.total = res.data['len']
          }
        }
        this.$Spin.hide()
      })
      .catch(err => {
        this.$config.err_notice(this, err)
        this.$Spin.hide()
      })
    },

    exportdata () {
      this.onQuerySql(true)
    },

    onSelectTree (nodes) {
      // 选择树节点
      let node = nodes[0]
      if (node.children) {
        // 点击数据库
        this.onChangeDatabase(node)
        return
      }
      for (let database of this.table_tree[0].children) {
        for (let table of database.children) {
          if (table.title === node.title && table.nodeKey === node.nodeKey) {
            this.input.database = database.title
            this.input.table = table.title
          }
        }
      }
      // 展示 table 数据
      axios.get(`${this.$config.url}/query/table?connection=${this.input.connection}&database=${this.input.database}&table=${this.input.table}`)
        .then(res => {
          if (res.data['error']) {
            this.$config.err_notice(this, res.data['error'])
          } else {
            // this.columnsName = res.data['title']
            // this.responses.query_results = res.data['data']
            this.responses.fields = res.data.field
            this.responses.indexs = res.data.idx
            // this.query_results_current_page = this.responses.query_results.slice(0, 10)
            // this.total = res.data['len']
          }
        })
    },

    ClearForm () {
      this.input.sql = ''
    },

    get_databases () {
      axios.get(`${this.$config.url}/query/databases?connection=${this.input.connection}`)
        .then(res => {
          this.table_tree = res.data.info
          let tWord = this.$config.highlight.split('|')
          for (let i of tWord) {
            this.wordList.push({ 'vl': i, 'meta': '关键字' })
          }
          this.wordList = this.wordList.concat(res.data.highlight)
          res.data['status'] === 1 ? this.export_data = true : this.export_data = false
      })
    }
  },

  mounted () {
    axios.put(`${this.$config.url}/workorder/connection`, {'permissions_type': 'query'})
      .then(res => {
        this.allowed_connections = res.data['connection']
        this.responses.cabinets = res.data['custom']
        this.ScreenConnection(DEFAULT_COMPUTER_ROOM)
      })
      .catch(error => {
        this.$config.err_notice(this, error)
      })
    for (let i of this.$config.highlight.split('|')) {
      this.wordList.push({'vl': i, 'meta': '关键字'})
    }
  }
}
</script>

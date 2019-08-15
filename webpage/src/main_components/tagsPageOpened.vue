<style lang="less">
  @import '../main.less';
</style>
<template>
  <div>
    <div>
      <div class="close-all-tag-con">
        <Dropdown transfer @on-click="handleTagsOption">
          <Button size="small" type="primary">
            标签开关
            <Icon type="arrow-down-b"></Icon>
          </Button>
          <DropdownMenu slot="list">
            <DropdownItem name="clearAll">关闭所有</DropdownItem>
            <DropdownItem name="clearOthers">关闭其他</DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </div>
    </div>
    <div>
      <transition-group name="taglist-moving-animation">
        <Tag
          type="dot"
          v-for="item in pageTagsList" 
          :key="item.name+item.window||''" 
          :name="item.name+'-'+item.window"
          :closable="item.name==='home_index'?false:true"
          :color="item.children?(item.children[0].name===$store.state.currentPageName?'primary':'default'):(item.name===$store.state.currentPageName && item.window==$store.state.currentPageWindow?'primary':'default')"
          @on-close="closePage"
          @click.native="linkTo(item.name, item.title, item.window)"
        >
          {{ item.connection ? item.title + '-' + item.connection : (item.window ? item.title + '-' + item.window : item.title) }}
        </Tag>
      </transition-group>
    </div>
  </div>
</template>

<script>
import util from '../libs/util';
  /*
    interface IPageTag {
      title: string
      path: string
      name: string
      window?: number
      connection?: string
    }
  */
  export default {
    name: 'tagsPageOpened',
    data () {
      return {
        tagBodyLeft: 0
      }
    },
    props: {
      pageTagsList: Array  // IPageTag[]
    },
    computed: {
      title () {
        return this.$store.state.currentTitle
      }
    },
    methods: {
      closePage (event, fullname) {
        this.$store.commit('removeTag', fullname)
        if (this.currentPageName === name) {
          let lastPageName = ''
          if (this.$store.state.pageOpenedList.length > 1) {
            lastPageName = this.$store.state.pageOpenedList[1].name
          } else {
            lastPageName = this.$store.state.pageOpenedList[0].name
          }
          this.$router.push({
            name: lastPageName
          })
          this.$store.commit('Breadcrumbset', lastPageName)
          this.$store.state.currentPageName = lastPageName
        }
        util.saveTags(this)
      },

      linkTo (name, title, window) {
        this.$router.push({
          name: name,
          params: {
            window: window
          }
        })
        this.$store.commit('Breadcrumbset', name)
        this.$store.state.currentPageName = name
        this.$store.state.currentPageWindow = window
      },
      handleTagsOption (type) {
        if (type === 'clearAll') {
          this.$store.commit('clearAllTags')
          this.$router.push({
            name: 'home_index'
          })
        } else {
          this.$store.commit('clearOtherTags', this)
        }
        this.tagBodyLeft = 0
      }
    },
    watch: {
      '$route' (to) {
        this.$store.state.currentPageName = to.name
        this.$store.state.currentPageWindow = to.params.window
      }
    }

  }
</script>

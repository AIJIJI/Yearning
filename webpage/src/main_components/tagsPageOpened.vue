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
          v-for="item in pageTagsList" :key="item.name+item.window||''" :name="item.name+'-'+item.window"
          type="dot"
          :closable="item.name==='home_index'?false:true"
          :color="item.children?(item.children[0].name===currentPageName?'primary':'default'):(item.name===currentPageName && item.window==currentPageWindow?'primary':'default')"
          @on-close="closePage"
          @click.native="linkTo(item.name, item.title, item.window)"
        >
          {{ item.window ? item.title + '-' + item.window : item.title }}
        </Tag>
      </transition-group>
    </div>
  </div>
</template>

<script>
  /*
    interface IPageTag {
      title: string
      path: string
      name: string
      window?: number
    }
  */
  export default {
    name: 'tagsPageOpened',
    data () {
      console.log(this.$route)
      return {
        currentPageName: this.$route.name,
        currentPageWindow: this.$route.params.window,
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
      closePage (event, name) {
        this.$store.commit('removeTag', name)
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
      },
      linkTo (name, title, window) {
        console.log()
        console.log({ name, title, window, pageList: this.pageTagsList, currentPageWindow: this.currentPageWindow, currentPageName: this.currentPageName })
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
        this.currentPageName = to.name
        this.currentPageWindow = to.params.window
      }
    }
  }
</script>

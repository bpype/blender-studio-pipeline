import DefaultTheme from 'vitepress/theme-without-fonts'
// TODO: consider adding Sass compile instead
import './web-assets-main-dark-compiled.css'
import './custom.css'
import LayoutNavBarGlobal from './LayoutNavBarGlobal.vue'

export default {
  extends: DefaultTheme,
  // Inject component LayoutNavBarGlobal
  Layout: LayoutNavBarGlobal
}

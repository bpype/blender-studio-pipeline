import DefaultTheme from 'vitepress/theme-without-fonts'
// Import style Web Assets dark compiled
import './web-assets-main-dark-compiled.css'
import './custom.css'
import LayoutNavBarGlobal from './LayoutNavBarGlobal.vue'

export default {
  extends: DefaultTheme,
  // Inject component LayoutNavBarGlobal
  Layout: LayoutNavBarGlobal
}

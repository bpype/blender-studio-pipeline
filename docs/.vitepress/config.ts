import { defineConfig } from 'vitepress'
import { html5Media } from 'markdown-it-html5-media'

const studioURL = 'https://studio.blender.org'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: '/pipeline/',
  title: "Blender Studio",
  description: "Documentation for the Blender Studio pipeline and tools.",
  lastUpdated: true,
  cleanUrls: true,
  srcExclude: ['**/README',],
  head: [
    [
      'script',
      {
        defer: '',
        'data-domain': 'studio.blender.org',
        src: 'https://analytics.blender.org/js/script.js'
      }
    ],
  ],
  themeConfig: {
    logo: {
      light: '/blender-studio-logo-black.svg',
      dark: '/blender-studio-logo-white.svg'
    },
    siteTitle: false,
    footer: {
      copyright: '(CC) Blender Foundation | studio.blender.org'
    },
    editLink: {
      pattern: 'https://projects.blender.org/studio/blender-studio-tools/_edit/master/docs/:path'
    },
    search: {
      provider: 'local'
    },
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Films', link: `${studioURL}/films` },
      { text: 'Training', link: `${studioURL}/training` },
      { text: 'Blog', link: `${studioURL}/blog` },
      { text: 'Pipeline', link: '/' },
      { text: 'Characters', link: `${studioURL}/characters`, }
    ],

    sidebar: [
      {
        text: 'Pipeline Overview',
        items: [
          { text: 'Introduction', link: '/pipeline-overview/introduction'},
          { text: 'Design Principles', link: '/pipeline-overview/design-principles'},
          { 
            text: 'Organization', 
            collapsed: true,
            items: [
              { text: 'Infrastructure', link: '/pipeline-overview/organization/infrastructure'},
              { text: 'Task Review', link: '/pipeline-overview/organization/task-review'},
            ]
          },
          {             
            text: 'Pre-Production', 
            collapsed: true,
            items: [
              { text: 'Storyboard', link: '/pipeline-overview/pre-production/storyboard'},
              { text: 'Editorial and Previz', link: '/pipeline-overview/pre-production/editorial-and-previz'},
              { text: 'Research and Development', link: '/pipeline-overview/pre-production/research-and-development'},
              { text: 'Concept and Design', link: '/pipeline-overview/pre-production/concept-and-design'},
            ]
          },
          { 
            text: 'Asset Creation', 
            collapsed: true,
            items: [
              { text: 'Modeling and Sculpting', link: '/pipeline-overview/asset-creation/modeling'},
              { text: 'Shading', link: '/pipeline-overview/asset-creation/shading'},
              { text: 'Rigging', link: '/pipeline-overview/asset-creation/rigging'},
              { text: 'Animation Testing', link: '/pipeline-overview/asset-creation/animation-testing'},
              { text: '2D Assets', link: '/pipeline-overview/asset-creation/2d-assets'},
            ]
          },
          { 
            text: 'Shot Production', 
            collapsed: true,
            items: [
              { text: 'Shot Assembly', link: '/pipeline-overview/shot-production/shot-assembly'},
              { text: 'Layout', link: '/pipeline-overview/shot-production/layout'},
              { text: 'Animation', link: '/pipeline-overview/shot-production/animation'},
              { text: 'Lighting', link: '/pipeline-overview/shot-production/lighting'},
              { text: 'Effects', link: '/pipeline-overview/shot-production/effects'},
              { text: 'Rendering', link: '/pipeline-overview/shot-production/rendering'},
              { text: 'Coloring', link: '/pipeline-overview/shot-production/coloring'},
            ]
          },
          { text: 'Publishing', link: '/pipeline-overview/publishing'},
        ]
      },
      {
        text: 'Add-ons',
        link:'/addons/overview',

        collapsed: true,
        items: [
          { text: 'Anim Cupboard', link: '/addons/anim_cupboard'},
          { text: 'Asset Pipeline', link: '/addons/asset_pipeline'},
          { text: 'Blender Kitsu', link: '/addons/blender_kitsu'},
          { text: 'Blender SVN', link: '/addons/blender_svn'},
          { text: 'Blender Gizmos', link: '/addons/bone_gizmos'},
          { text: 'Cache Manager', link: '/addons/cache_manager'},
          { text: 'Contact Sheet', link: '/addons/contactsheet'},
          { text: 'Easy Weights', link: '/addons/easy_weights'},
          { text: 'Geonode Shapekeys', link: '/addons/geonode_shapekeys'},
          { text: 'Grase Converter', link: '/addons/grease_converter'},
          { text: 'Lattice Magic', link: '/addons/lattice_magic'},
          { text: 'Lighting Overrider', link: '/addons/lighting_overrider'},
          { text: 'Pose Shape Keys', link: '/addons/pose_shape_keys'},
          { text: 'Render Review', link: '/addons/render_review'},
        ]
      },
      {
        text: 'Naming Conventions',
        collapsed: true,
        items: [
          { text: 'Introduction', link: '/naming-conventions/introduction'},
          { text: 'File Types', link: '/naming-conventions/file-types'},
          { text: 'In-file Prefixes', link: '/naming-conventions/in-file-prefixes'},
          { text: 'Examples', link: '/naming-conventions/examples'},
          { text: 'Shared Folder Structure', link: '/naming-conventions/shared-folder-structure'},
          { text: 'SVN Folder Structure', link: '/naming-conventions/svn-folder-structure'},
        ]
      },
      {
        text: 'User Guide',
        collapsed: false,
        items: [
          {
            text: 'Project Setup',
            collapsed: true,
            items: [
              { text: 'Intro', link: '/user-guide/project-setup/intro' },
              { text: 'SVN', link: '/user-guide/project-setup/svn' },
              {
                text: 'Workstation',
                collapsed: true,
                items: [
                  { text: 'Introduction', link: '/user-guide/project-setup/workstations/introduction' },
                  { text: 'Installing Software', link: '/user-guide/project-setup/workstations/installing-software' },
                  { text: 'Running Blender', link: '/user-guide/project-setup/workstations/running-blender' },
                  { text: 'Troubleshooting', link: '/user-guide/project-setup/workstations/troubleshooting' },
                ],
              },
            ],
          },
          {
            text: 'Organization',
            collapsed: true,
            items: [
              { text: 'Planning', link: '/user-guide/organization/planning' },
              { text: 'Task Review', link: '/user-guide/organization/task-review' },
            ],
          },
          { text: 'Debugging', link: '/user-guide/debugging' },
          { text: 'Kitsu', link: '/user-guide/kitsu' },
        ],
      },
      
      {
        text: 'TD Guide',
        collapsed: false,
        items: [
          {text: 'Project Setup', link: '/td-guide/project-setup'},
          {
            text: 'Workstation',
            collapsed: true,
            items: [
              { text: 'Overview', link: '/td-guide/workstations/overview'},
              { text: 'Installation', link: '/td-guide/workstations/installation'},
              { text: 'Maintenance', link: '/td-guide/workstations/maintaince'},
              { text: 'Render Farm', link: '/td-guide/workstations/render_farm'},

            ]
          },
        ]
      },
      {
        text: 'Archive',
        collapsed: true,
        items: [
          {text: 'Pipeline Proposal', link: '/archive/pipeline-proposal-2019/introduction'},
          {text: 'Attact Updates', link: '/archive/pipeline-proposal-2019/attract-improvements'},
          {text: 'Task Companion Add-on', link: '/archive/pipeline-proposal-2019/task-companion-add-on'},
          {text: 'Shot Caching', link: '/archive/pipeline-proposal-2019/shot-caching/introduction', items: [
            {text: 'Add-on', link: '/archive/pipeline-proposal-2019/shot-caching/add-on', items: [
              {text: 'User Stories', link: '/archive/pipeline-proposal-2019/shot-caching/user-stories'},
              {text: 'Structural Ideas', link: '/archive/pipeline-proposal-2019/shot-caching/structural-ideas'}
            ]},
            {text: 'Issues', link: '/archive/pipeline-proposal-2019/shot-caching/issues'},
          ]},
          {text: 'Asset Publishing', link: '/archive/pipeline-proposal-2019/asset-publishing/introduction'},
          {text: 'Character Pipeline Assistant', link: '/archive/pipeline-proposal-2019/asset-publishing/character-pipeline-assistant'},
        ],
      }
    ],
  },
  markdown: {
    config: (md) => {
      // Enable the markdown-it-html5-media plugin
      md.use(html5Media)
    }
  }

})

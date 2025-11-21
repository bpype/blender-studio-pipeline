// Imports for overriding internal components
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vitepress'
import { html5Media } from 'markdown-it-html5-media'

const studioURL = 'https://studio.blender.org'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: '/tools/',
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
      /*
      Logo is injected from Vue component NavBarGlobal
      light: '/blender-studio-logo-black.svg',
      dark: '/blender-studio-logo-white.svg'
      */
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
      /*
      Nav is injected from Vue component NavBarGlobal
      { text: 'Films', link: `${studioURL}/films` },
            { text: 'Training', link: `${studioURL}/training` },
            { text: 'Blog', link: `${studioURL}/blog` },
            { text: 'Pipeline', link: '/' },
            { text: 'Characters', link: `${studioURL}/characters`, }
      */
    ],

    sidebar: [
      {
        text: 'Blender Studio Tools',
        items: [
          { text: 'Introduction', link: '/overview/introduction'},
          { text: 'Design Principles', link: '/overview/design-principles'},

        ]
      },
      {
        text: 'Artist Guide',
        collapsed: false,
        items: [
          {text: 'Project Overview', link: '/artist-guide/project_tools/project-overview' },
          {text: 'Project Blender', link: '/artist-guide/project_tools/project-blender' },
          {
            text: 'Project Tools',
            collapsed: true,
            items: [
              
              {
                text: 'Project Usage',
                collapsed: true,
                items: [
                  {text: 'Introduction', link: '/artist-guide/project_tools/project-usage'},
                  {text: 'Prepare Edit', link: '/artist-guide/project_tools/usage-sync-edit'},
                  {text: 'Creating Assets', link: '/artist-guide/project_tools/usage-asset'},
                  {text: 'Building Shots', link: '/artist-guide/project_tools/usage-build-shot'},
                  {text: 'Playblast Shot', link: '/artist-guide/project_tools/usage-playblast'},
                  {text: 'Import Playblast', link: '/artist-guide/project_tools/usage-import-playblast'},
                  {text: 'Update Shot', link: '/artist-guide/project_tools/usage-update-shot'},
                  {text: 'Flamenco Render', link: '/artist-guide/project_tools/usage-render-flamenco'},
                  {text: 'Render Review', link: '/artist-guide/project_tools/usage-render-review'},
                  {text: 'Final Render', link: '/artist-guide/project_tools/usage-final-render'},
                ],
              },
            ],
          },
          { text: 'Debugging', link: '/artist-guide/debugging' },
          { text: 'Kitsu', link: '/artist-guide/kitsu' },
          {
            text: 'Pre-Production',
            collapsed: true,
            items: [
              { text: 'Storyboard', link: '/artist-guide/pre-production/storyboard'},
              { text: 'Editorial', link: '/artist-guide/pre-production/editorial'},
              { text: 'Previz', link: '/artist-guide/pre-production/previz'},
              { text: 'Research and Development', link: '/artist-guide/pre-production/research-and-development'},
              { text: 'Concept and Design', link: '/artist-guide/pre-production/concept-and-design'},
            ]
          },
          {
            text: 'Asset Creation',
            collapsed: true,
            items: [
              { text: 'Modeling and Sculpting', link: '/artist-guide/asset-creation/modeling'},
              { text: 'Shading', link: '/artist-guide/asset-creation/shading'},
              { text: 'Rigging', link: '/artist-guide/asset-creation/rigging'},
              { text: 'Animation Testing', link: '/artist-guide/asset-creation/animation-testing'},
              { text: '2D Assets', link: '/artist-guide/asset-creation/2d-assets'},
            ]
          },
          {
            text: 'Shot Production',
            collapsed: true,
            items: [
              { text: 'Shot Assembly', link: '/artist-guide/shot-production/shot-assembly'},
              { text: 'Layout', link: '/artist-guide/shot-production/layout'},
              { text: 'Animation', link: '/artist-guide/shot-production/animation'},
              { text: 'Lighting', link: '/artist-guide/shot-production/lighting'},
              { text: 'Effects', link: '/artist-guide/shot-production/effects'},
              { text: 'Rendering', link: '/artist-guide/shot-production/rendering'},
              { text: 'Coloring', link: '/artist-guide/shot-production/coloring'},
            ]
          },
        ],
      },

      {
        text: 'IT and TD Guide',
        collapsed: true,
        items: [
          {text: 'Introduction', link: '/td-guide/introduction'},
          {text: 'Quick Start', link: '/td-guide/quick-start'},
          {text: 'Folder Structure', link: '/td-guide/folder_structure_overview'},
          {text: 'Python', link: '/td-guide/python'},
          {text: 'Kitsu', link: '/td-guide/kitsu_server'},
          {text: 'Setup Assistant', link: '/td-guide/setup_assistant'},
          {text: 'Deployment Assistant', link: '/td-guide/deployment_assistant'},
          {
            text: 'Manual Configuration',
            collapsed: true,
            items: [
              {text: 'Folder Structure Setup', link: '/td-guide/folder_structure_setup'},
              {
                text: 'Shared',
                collapsed: true,
                items: [
                  {text: 'Syncthing Setup', link: '/td-guide/syncthing-setup'},
                  {text: 'Populating Shared', link: '/td-guide/populating_shared'},
                ],
              },
              {
                text: 'SVN',
                collapsed: true,
                items: [
                  {text: 'SVN Setup', link: '/td-guide/svn-setup'},
                  {text: 'Populating SVN', link: '/td-guide/populating_svn'},
                ],
              },
              {
                text: 'Blender',
                collapsed: true,
                items: [
                  {text: 'Blender Setup', link: '/td-guide/blender_setup'},
                  {text: 'Extensions Setup', link: '/td-guide/extensions_setup'},
                  {text: 'Add-Ons Preferences', link: '/td-guide/addon_preferences'},
                ],
              },
            ],
          },
          {text: 'Flamenco', link: '/td-guide/flamenco_setup'},

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
          { text: 'Blender Log', link: '/addons/blender_log'},
          { text: 'Blender SVN', link: '/addons/blender_svn'},
          { text: 'Bone Gizmos', link: '/addons/bone_gizmos'},
          { text: 'Brushstroke Tools', link: '/addons/brushstroke_tools'},
          { text: 'Cache Manager', link: '/addons/cache_manager'},
          {
            text: 'CloudRig',
            collapsed: true,
            items: [
              {text: 'Introduction', link: '/addons/cloudrig/introduction'},
              {text: 'Component Types', link: '/addons/cloudrig/cloudrig-types'},
              {text: 'Generator Parameters', link: '/addons/cloudrig/generator-parameters'},
              {text: 'Rig UI', link: '/addons/cloudrig/rig-ui'},
              {text: 'Properties UI', link: '/addons/cloudrig/properties-ui'},
              {text: 'Organizing Bones', link: '/addons/cloudrig/organizing-bones'},
              {text: 'Actions', link: '/addons/cloudrig/actions'},
              {text: 'Troubleshooting', link: '/addons/cloudrig/troubleshooting'},
              {text: 'Constraint Relinking', link: '/addons/cloudrig/constraint-relinking'},
              {text: 'Workflow Boosters', link: '/addons/cloudrig/workflow-enhancements'},
              {text: 'Contribute', link: '/addons/cloudrig/code'},
            ],
          },
          { text: 'Contact Sheet', link: '/addons/contactsheet'},
          { text: 'Easy Weight', link: '/addons/easy_weight'},
          { text: 'Geonode Shapekeys', link: '/addons/geonode_shapekeys'},
          { text: 'Lattice Magic', link: '/addons/lattice_magic'},
          { text: 'Lighting Overrider', link: '/addons/lighting_overrider'},
          { text: 'Pose Shape Keys', link: '/addons/pose_shape_keys'},
        ]
      },
      {
        text: 'Naming Conventions',
        collapsed: true,
        items: [
          { text: 'Introduction', link: '/naming-conventions/introduction'},
          { text: 'File Types', link: '/naming-conventions/file-types'},
          { text: 'In-file Naming', link: '/naming-conventions/datablock-names'},
          { text: 'Examples', link: '/naming-conventions/examples'},
          { text: 'Shared Folder Structure', link: '/naming-conventions/shared-folder-structure'},
          { text: 'SVN Folder Structure', link: '/naming-conventions/svn-folder-structure'},
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
      },
      {
        text: 'Gentoo',
        collapsed: true,
        items: [
          {
            text: 'TD',
            collapsed: false,
            items: [
              { text: 'Overview', link: '/gentoo/td/overview'},
              { text: 'Installation', link: '/gentoo/td/installation'},
              { text: 'Maintenance', link: '/gentoo/td/maintaince'},
              { text: 'Render Farm', link: '/gentoo/td/render_farm'},
              { text: 'Troubleshooting', link: '/gentoo/td/troubleshooting' },
            ],
          },

          {
            text: 'User',
            collapsed: false,
            items: [
              { text: 'Introduction', link: '/gentoo/user/introduction' },
              { text: 'Installing Software', link: '/gentoo/user/installing-software' },
              { text: 'Running Blender', link: '/gentoo/user/running-blender' },
              { text: 'SVN', link: '/gentoo/user/svn' },

            ]
          },
        ],
      },
    ],
  },
  markdown: {
    config: (md) => {
      // Enable the markdown-it-html5-media plugin
      md.use(html5Media)
    }
  },
  // Override internal component 'VPNavBar'
  vite: {
    resolve: {
      alias: [
        {
          find: /^.*\/VPNavBar\.vue$/,
          replacement: fileURLToPath(
            new URL('./components/NavBarGlobal.vue', import.meta.url)
          )
        }
      ]
    }
  }
})

// Imports for overriding internal components
import { fileURLToPath, URL } from 'node:url'

import { html5Media } from 'markdown-it-html5-media'
import { defineConfig } from 'vitepress'

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
          { text: 'Welcome', link: '/overview/introduction' },
          { text: 'Design Principles', link: '/overview/design-principles' },
        ]
      },
      {
        text: 'Pipeline',
        collapsed: false,
        items: [
          { text: 'Getting Started', link: '/pipeline/getting-started.md' },
          { text: 'Workflow',
            link: '/pipeline/workflow.md',
            collapsed: true,
            items:[
              // { text: 'Introduction', link: '/pipeline/project-workflow/project-usage' },
              { text: 'Prepare Edit', link: '/pipeline/project-workflow/usage-sync-edit' },
              { text: 'Creating Assets', link: '/pipeline/project-workflow/usage-asset' },
              { text: 'Building Shots', link: '/pipeline/project-workflow/usage-build-shot' },
              { text: 'Publish Shot', link: '/pipeline/project-workflow/usage-playblast' },
              { text: 'Import Publish', link: '/pipeline/project-workflow/usage-import-playblast' },
              { text: 'Update Shot', link: '/pipeline/project-workflow/usage-update-shot' },
              { text: 'Render Shot', link: '/pipeline/project-workflow/usage-render-flamenco' },
              { text: 'Render Review', link: '/pipeline/project-workflow/usage-render-review' },
              { text: 'Import Render', link: '/pipeline/project-workflow/usage-import-render' },
              { text: 'Final Render', link: '/pipeline/project-workflow/usage-final-render' },
            ]
          },
          {
            text: 'Pre-Production',
            collapsed: true,
            items: [
              { text: 'Storyboard', link: '/artist-guide/pre-production/storyboard' },
              { text: 'Editorial', link: '/artist-guide/pre-production/editorial' },
              { text: 'Previz', link: '/artist-guide/pre-production/previz' },
              { text: 'Research and Development', link: '/artist-guide/pre-production/research-and-development' },
              { text: 'Concept and Design', link: '/artist-guide/pre-production/concept-and-design' },
            ]
          },
          {
            text: 'Asset Creation',
            collapsed: true,
            items: [
              { text: 'Modeling and Sculpting', link: '/artist-guide/asset-creation/modeling' },
              { text: 'Shading', link: '/artist-guide/asset-creation/shading' },
              { text: 'Rigging', link: '/artist-guide/asset-creation/rigging' },
              { text: 'Animation Testing', link: '/artist-guide/asset-creation/animation-testing' },
              { text: '2D Assets', link: '/artist-guide/asset-creation/2d-assets' },
            ]
          },
          {
            text: 'Shot Production',
            collapsed: true,
            items: [
              { text: 'Shot Assembly', link: '/artist-guide/shot-production/shot-assembly' },
              { text: 'Layout', link: '/artist-guide/shot-production/layout' },
              { text: 'Animation', link: '/artist-guide/shot-production/animation' },
              { text: 'Lighting', link: '/artist-guide/shot-production/lighting' },
              { text: 'Effects', link: '/artist-guide/shot-production/effects' },
              { text: 'Rendering', link: '/artist-guide/shot-production/rendering' },
              { text: 'Coloring', link: '/artist-guide/shot-production/coloring' },
            ]
          },
          {
            text: 'Operations',
            collapsed: true,

            items: [
              { text: 'Launching Blender', link: '/tools/scripts/project-tools/project-blender' },
              { text: 'Git Usage', link: '/pipeline/operations/git-usage' },
              { text: 'Kitsu Management', link: '/pipeline/operations/kitsu' },
              { text: 'Debugging Overrides', link: '/pipeline//operations/debugging' },
              {
                text: 'File & Naming Conventions',
                collapsed: true,
                link: '/pipeline//file-and-naming-conventions/intro',
                items: [
                  { text: 'In-file Naming', link: '/pipeline//file-and-naming-conventions/datablock-names' },
                  { text: 'File Types', link: '/pipeline//file-and-naming-conventions/file-types' },
                  { text: 'Project Files Structure', link: '/pipeline//file-and-naming-conventions/project-files-folder-structure' },
                  { text: 'Shared Folder Structure', link: '/pipeline//file-and-naming-conventions/shared-folder-structure' },
                ]
              },
            ]
          },
        ],
      },
      {
        text: 'Tools',
        collapsed: false,

        items: [

          {
            text: 'Add-ons',
            link: '/addons/overview',
            items: [
              { text: 'Anim Cupboard', link: '/addons/anim_cupboard' },
              { text: 'Asset Pipeline', link: '/addons/asset_pipeline' },
              { text: 'Blender Kitsu', link: '/addons/blender_kitsu' },
              {
                text: 'Expo Manager',
                collapsed: true,
                items: [
                  { text: 'Introduction', link: '/addons/expo-manager/introduction.md' },
                  { text: 'Configuration', link: '/addons/expo-manager/configuration.md' },
                  { text: 'Context', link: '/addons/expo-manager/context.md' },
                  { text: 'File Builder', link: '/addons/expo-manager/file_builder.md' },
                  { text: 'Shots', link: '/addons/expo-manager/shot.md' },
                  { text: 'Assets', link: '/addons/expo-manager/asset.md' },
                  { text: 'Editing', link: '/addons/expo-manager/edit.md' },
                  { text: 'Render Review', link: '/addons/expo-manager/render-review.md' },
                  { text: 'Conventions', link: '/addons/expo-manager/conventions.md' },
                  { text: 'Backups', link: '/addons/expo-manager/backups.md' },

                ]
              },
              { text: 'Blender Log', link: '/addons/blender_log' },
              { text: 'Brushstroke Tools', link: '/addons/brushstroke_tools' },
              {
                text: 'CloudRig',
                collapsed: true,
                items: [
                  { text: 'Introduction', link: '/addons/cloudrig/introduction' },
                  { text: 'Component Types', link: '/addons/cloudrig/cloudrig-types' },
                  { text: 'Generator Parameters', link: '/addons/cloudrig/generator-parameters' },
                  { text: 'Rig UI', link: '/addons/cloudrig/rig-ui' },
                  { text: 'Properties UI', link: '/addons/cloudrig/properties-ui' },
                  { text: 'Organizing Bones', link: '/addons/cloudrig/organizing-bones' },
                  { text: 'Actions', link: '/addons/cloudrig/actions' },
                  { text: 'Troubleshooting', link: '/addons/cloudrig/troubleshooting' },
                  { text: 'Constraint Relinking', link: '/addons/cloudrig/constraint-relinking' },
                  { text: 'Workflow Boosters', link: '/addons/cloudrig/workflow-enhancements' },
                  { text: 'Contribute', link: '/addons/cloudrig/code' },
                ],
              },
              { text: 'Contact Sheet', link: '/addons/contactsheet' },
              { text: 'Easy Weight', link: '/addons/easy_weight' },
              { text: 'Geonode Shapekeys', link: '/addons/geonode_shapekeys' },
              { text: 'Lattice Magic', link: '/addons/lattice_magic' },
              { text: 'Lighting Overrider', link: '/addons/lighting_overrider' },
              { text: 'Pose Shape Keys', link: '/addons/pose_shape_keys' },
            ]
          },
        ]
      },

      {
        text: 'Studio Setup',
        collapsed: true,
        items: [
          { text: 'Overview', link: '/studio-setup/introduction' },
          { text: 'Repository', link: '/studio-setup/repository' },
          { text: 'Folder Structure', link: '/studio-setup/folder_structure_overview' },
          { text: 'Python', link: '/studio-setup/python' },
          { text: 'Kitsu', link: '/studio-setup/kitsu_server' },
          { text: 'Git Setup', link: '/studio-setup/git-setup' },
          { text: 'Syncthing Setup', link: '/studio-setup/syncthing-setup' },
          {
            text: 'Project Tools',
            link: '/tools/scripts/project-tools/overview',
            collapsed: true,
            items: [
              { text: 'Populating Shared', link: '/tools/scripts/project-tools/folder-structure-setup/populating_shared' },
              { text: 'Populating Project Files', link: '/tools/scripts/project-tools/folder-structure-setup/populating_project_files' },
              { text: 'Blender Setup', link: '/tools/scripts/project-tools/project-blender' },
              { text: 'Extensions Setup', link: '/tools/scripts/project-tools/extensions_setup' },
              { text: 'Add-ons Preferences', link: '/tools/scripts/project-tools/addon_preferences' },
            ],
          },
          { text: 'Flamenco', link: '/studio-setup/flamenco_setup' },


          {
            text: 'Gentoo',
            collapsed: true,
            items: [
              { text: 'Overview', link: '/gentoo/td/overview' },
              {
                text: 'Setup',
                collapsed: false,
                items: [
                  { text: 'Installation', link: '/gentoo/td/installation' },
                  { text: 'Maintenance', link: '/gentoo/td/maintaince' },
                  { text: 'Render Farm', link: '/gentoo/td/render_farm' },
                  { text: 'Troubleshooting', link: '/gentoo/td/troubleshooting' },
                ],
              },
              {
                text: 'Usage',
                collapsed: false,
                items: [
                  { text: 'Introduction', link: '/gentoo/user/introduction' },
                  { text: 'Installing Software', link: '/gentoo/user/installing-software' },
                  { text: 'Running Blender', link: '/gentoo/user/running-blender' },

                ]
              },
            ],
          },
        ]
      },

      {
        text: 'Archive',
        collapsed: true,
        items: [
          { text: 'Blender Kitsu', link: '/addons/blender_kitsu' },
          { text: 'Pipeline Proposal', link: '/archive/pipeline-proposal-2019/introduction' },
          { text: 'Attact Updates', link: '/archive/pipeline-proposal-2019/attract-improvements' },
          { text: 'Task Companion Add-on', link: '/archive/pipeline-proposal-2019/task-companion-add-on' },
          {
            text: 'Shot Caching', link: '/archive/pipeline-proposal-2019/shot-caching/introduction', items: [
              {
                text: 'Add-on', link: '/archive/pipeline-proposal-2019/shot-caching/add-on', items: [
                  { text: 'User Stories', link: '/archive/pipeline-proposal-2019/shot-caching/user-stories' },
                  { text: 'Structural Ideas', link: '/archive/pipeline-proposal-2019/shot-caching/structural-ideas' }
                ]
              },
              { text: 'Issues', link: '/archive/pipeline-proposal-2019/shot-caching/issues' },
            ]
          },
          { text: 'Asset Publishing', link: '/archive/pipeline-proposal-2019/asset-publishing/introduction' },
          { text: 'Character Pipeline Assistant', link: '/archive/pipeline-proposal-2019/asset-publishing/character-pipeline-assistant' },
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

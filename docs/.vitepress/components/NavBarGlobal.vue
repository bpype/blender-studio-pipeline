<template>
  <div class="nav-global">
    <div class="nav-global-container">
      <nav>
        <a href="/" class="nav-global-logo">
          <svg fill-rule="nonzero" viewBox="0 0 200 162.05">
            <path d="M61.1 104.56c.05 2.6.88 7.66 2.12 11.61a61.27 61.27 0 0 0 13.24 22.92 68.39 68.39 0 0 0 23.17 16.64 74.46 74.46 0 0 0 30.42 6.32 74.52 74.52 0 0 0 30.4-6.42 68.87 68.87 0 0 0 23.15-16.7 61.79 61.79 0 0 0 13.23-22.97 58.06 58.06 0 0 0 2.07-25.55 59.18 59.18 0 0 0-8.44-23.1 64.45 64.45 0 0 0-15.4-16.98h.02L112.76 2.46l-.16-.12c-4.09-3.14-10.96-3.13-15.46.02-4.55 3.18-5.07 8.44-1.02 11.75l-.02.02 26 21.14-79.23.08h-.1c-6.55.01-12.85 4.3-14.1 9.74-1.27 5.53 3.17 10.11 9.98 10.14v.02l40.15-.07-71.66 55-.27.2c-6.76 5.18-8.94 13.78-4.69 19.23 4.32 5.54 13.51 5.55 20.34.03l39.1-32s-.56 4.32-.52 6.91zm100.49 14.47c-8.06 8.2-19.34 12.86-31.54 12.89-12.23.02-23.5-4.6-31.57-12.79-3.93-4-6.83-8.59-8.61-13.48a35.57 35.57 0 0 1 2.34-29.25 39.1 39.1 0 0 1 9.58-11.4 44.68 44.68 0 0 1 28.24-9.85 44.59 44.59 0 0 1 28.24 9.77 38.94 38.94 0 0 1 9.58 11.36 35.58 35.58 0 0 1 4.33 14.18 35.1 35.1 0 0 1-1.98 15.05 37.7 37.7 0 0 1-8.61 13.52zm-57.6-27.91a23.55 23.55 0 0 1 8.55-16.68 28.45 28.45 0 0 1 18.39-6.57 28.5 28.5 0 0 1 18.38 6.57 23.57 23.57 0 0 1 8.55 16.67c.37 6.83-2.37 13.19-7.2 17.9a28.18 28.18 0 0 1-19.73 7.79c-7.83 0-14.84-3-19.75-7.8a23.13 23.13 0 0 1-7.19-17.88z"></path>
            </svg><strong>Blender Studio</strong>
        </a>

        <button class="nav-global-logo js-nav-global-dropdown-toggle" data-dropdown-id="nav-global-nav-links">
          <svg fill-rule="nonzero" viewBox="0 0 850.2 162.05">
            <path d="M61.1 104.56c.05 2.6.88 7.66 2.12 11.61a61.27 61.27 0 0 0 13.24 22.92 68.39 68.39 0 0 0 23.17 16.64 74.46 74.46 0 0 0 30.42 6.32 74.52 74.52 0 0 0 30.4-6.42 68.87 68.87 0 0 0 23.15-16.7 61.79 61.79 0 0 0 13.23-22.97 58.06 58.06 0 0 0 2.07-25.55 59.18 59.18 0 0 0-8.44-23.1 64.45 64.45 0 0 0-15.4-16.98h.02L112.76 2.46l-.16-.12c-4.09-3.14-10.96-3.13-15.46.02-4.55 3.18-5.07 8.44-1.02 11.75l-.02.02 26 21.14-79.23.08h-.1c-6.55.01-12.85 4.3-14.1 9.74-1.27 5.53 3.17 10.11 9.98 10.14v.02l40.15-.07-71.66 55-.27.2c-6.76 5.18-8.94 13.78-4.69 19.23 4.32 5.54 13.51 5.55 20.34.03l39.1-32s-.56 4.32-.52 6.91zm100.49 14.47c-8.06 8.2-19.34 12.86-31.54 12.89-12.23.02-23.5-4.6-31.57-12.79-3.93-4-6.83-8.59-8.61-13.48a35.57 35.57 0 0 1 2.34-29.25 39.1 39.1 0 0 1 9.58-11.4 44.68 44.68 0 0 1 28.24-9.85 44.59 44.59 0 0 1 28.24 9.77 38.94 38.94 0 0 1 9.58 11.36 35.58 35.58 0 0 1 4.33 14.18 35.1 35.1 0 0 1-1.98 15.05 37.7 37.7 0 0 1-8.61 13.52zm-57.6-27.91a23.55 23.55 0 0 1 8.55-16.68 28.45 28.45 0 0 1 18.39-6.57 28.5 28.5 0 0 1 18.38 6.57 23.57 23.57 0 0 1 8.55 16.67c.37 6.83-2.37 13.19-7.2 17.9a28.18 28.18 0 0 1-19.73 7.79c-7.83 0-14.84-3-19.75-7.8a23.13 23.13 0 0 1-7.19-17.88z"></path>
            <path d="M829.17 133.76h-15.9V64.39h15.13l.77 13.59zM850.07 79q-1.47-.25-3.14-.38-1.6-.13-3.2-.13-5.26 0-8.8 1.92-3.45 1.86-5.25 5.39-1.8 3.46-2.11 8.2l-3.66.07q0-8.78 2.31-15.77 2.3-6.99 6.92-11.1 4.62-4.1 11.54-4.1 1.35 0 3.02.26 1.66.26 2.5.58zm-76.55 56.04q-10.32 0-17.82-4.42-7.5-4.5-11.55-12.06-4.03-7.63-4.03-17.05v-2.63q0-10.84 4.1-18.85 4.1-8.08 11.22-12.5 7.18-4.43 16.22-4.43 10 0 16.6 4.36 6.6 4.3 9.88 12 3.27 7.62 3.27 17.69V104h-53.67V92.53h37.96v-1.22q-.13-4.04-1.54-7.56-1.4-3.53-4.49-5.7-3.01-2.19-8.07-2.19-5.07 0-8.53 2.89-3.46 2.82-5.26 8.01-1.8 5.13-1.8 12.12v2.63q0 5.9 2.19 10.58 2.18 4.68 6.34 7.43 4.17 2.7 9.94 2.7 5.58 0 9.87-2.18 4.36-2.18 7.5-6.29l8.34 8.34q-3.27 4.93-9.87 8.97-6.54 3.98-16.8 3.98zm-88.67 25.39h-15.9V64.39h14.68l1.22 13.33zm45-60.72q0 10.13-3.13 18.15-3.08 7.95-9.1 12.56-5.97 4.62-14.63 4.62-8.72 0-14.49-4.23-5.7-4.3-8.9-11.8-3.21-7.5-4.43-17.12v-4.55q1.22-10.26 4.42-17.89 3.2-7.7 8.91-11.99 5.71-4.36 14.3-4.36 8.79 0 14.81 4.43 6.03 4.42 9.1 12.37 3.15 7.95 3.15 18.47zm-15.9-1.34q0-6.22-1.6-11.29-1.53-5.06-5-8.01-3.4-2.95-8.9-2.95-3.98 0-6.87 1.35-2.88 1.28-4.87 3.65-1.92 2.37-3.01 5.64-1.1 3.2-1.54 7.05v11.6q.77 4.62 2.56 8.47 1.8 3.85 5.13 6.16 3.4 2.24 8.72 2.24 5.51 0 8.91-3.08 3.4-3.14 4.94-8.2 1.54-5.13 1.54-11.29zm-122.51.06q0-10.13 3.84-18.08 3.85-7.95 11.03-12.57 7.25-4.68 17.38-4.68 10.25 0 17.5 4.68 7.24 4.62 11.03 12.57 3.84 7.95 3.84 18.08v1.35q0 10.06-3.84 18.08-3.79 7.95-11.03 12.56-7.18 4.62-17.38 4.62-10.19 0-17.43-4.62-7.25-4.61-11.1-12.56-3.84-8.02-3.84-18.08zm15.9 1.35q0 6.15 1.73 11.28 1.73 5.07 5.32 8.14 3.65 3.08 9.42 3.08 5.71 0 9.3-3.08 3.65-3.07 5.32-8.14 1.73-5.13 1.73-11.28v-1.35q0-6.09-1.73-11.22-1.67-5.13-5.32-8.2-3.65-3.15-9.42-3.15-5.71 0-9.36 3.14-3.6 3.08-5.33 8.21-1.66 5.13-1.66 11.22zm-29.69 33.98h-15.9V35.28h15.9zm-56.67 1.28q-10.33 0-17.83-4.42-7.5-4.5-11.54-12.06-4.04-7.63-4.04-17.05v-2.63q0-10.84 4.1-18.85 4.11-8.08 11.23-12.5 7.18-4.43 16.22-4.43 10 0 16.6 4.36 6.6 4.3 9.88 12 3.27 7.62 3.27 17.69V104H495.2V92.53h37.96v-1.22q-.13-4.04-1.54-7.56-1.41-3.53-4.49-5.7-3.01-2.19-8.08-2.19-5.06 0-8.52 2.89-3.47 2.82-5.26 8.01-1.8 5.13-1.8 12.12v2.63q0 5.9 2.18 10.58t6.35 7.43q4.17 2.7 9.94 2.7 5.58 0 9.87-2.18 4.36-2.18 7.5-6.29l8.34 8.34q-3.27 4.93-9.88 8.97-6.54 3.98-16.8 3.98zM464.3 64.39h16.48l-23.98 69.37h-10.26l1.03-12.57zm-12.25 57 .77 12.37h-10.19l-24.17-69.37H435zm-65.88 13.65q-10.32 0-17.82-4.42-7.5-4.5-11.54-12.06-4.04-7.63-4.04-17.05v-2.63q0-10.84 4.1-18.85 4.1-8.08 11.22-12.5 7.18-4.43 16.22-4.43 10 0 16.6 4.36 6.61 4.3 9.88 12 3.27 7.62 3.27 17.69V104H360.4V92.53h37.95v-1.22q-.12-4.04-1.53-7.56-1.42-3.53-4.5-5.7-3-2.19-8.07-2.19t-8.53 2.89q-3.46 2.82-5.26 8.01-1.8 5.13-1.8 12.12v2.63q0 5.9 2.19 10.58 2.18 4.68 6.35 7.43 4.16 2.7 9.93 2.7 5.58 0 9.88-2.18 4.36-2.18 7.5-6.29l8.33 8.34q-3.27 4.93-9.87 8.97-6.54 3.98-16.8 3.98zm-107.64-1.28.12-13.27h19.75q8.6 0 14.36-3.72 5.77-3.72 8.72-10.65 2.95-6.98 2.95-16.67v-4.87q0-9.94-2.95-16.8-2.88-6.86-8.59-10.45-5.7-3.59-13.91-3.59h-20.84V40.41h20.84q12.5 0 21.93 5.51 9.48 5.52 14.8 15.45 5.33 9.94 5.33 23.34v4.74q0 13.47-5.32 23.4-5.33 9.94-14.94 15.46-9.56 5.45-22.38 5.45zm9.23 0h-16.54V40.4h16.54z"></path>
          </svg>
          <svg class="nav-global-icon nav-global-icon-dropdown-toggle" height="100px" width="100px" viewBox="0 0 1000 1000">
            <path d="m 206.53824,376.41174 a 42,42 0 0 1 71,-29 l 221,220 220,-220 a 42,42 0 1 1 59,59 l -250,250 a 42,42 0 0 1 -59,0 l -250,-250 a 42,42 0 0 1 -12,-30 z"></path>
          </svg>
        </button>

        <ul class="js-nav-global-dropdown nav-global-nav-links nav-global-dropdown" id="nav-global-nav-links">
          <!-- TODO: use constant studioURL for links -->
          <li>
            <a href="https://studio.blender.org/films">Films</a>
          </li>
          <li>
            <a href="https://studio.blender.org/training">Training</a>
          </li>
          <li>
            <a href="https://studio.blender.org/characters">Characters</a>
          </li>
          <li>
            <a href="/" class="nav-global-link-active">Pipeline</a>
          </li>
          <li>
            <a href="https://studio.blender.org/blog">Blog</a>
          </li>
        </ul>

        <ul class="nav-global-links-right">
          <li>
            <div class="nav-global-apps-dropdown-container">
              <button
                class="js-nav-global-dropdown-toggle"
                data-dropdown-id="nav-global-apps-menu"
              >
                <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                  <path d="m 150.5,899 a 50,50 0 0 1 -49,-50 V 749 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 749 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 749 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m -598,-299 a 50,50 0 0 1 -49,-50 V 450 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 450 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 450 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m -598,-299 a 50,50 0 0 1 -49,-50 V 151 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 151 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 151 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z"></path>
                </svg>
              </button>

              <div class="js-nav-global-dropdown nav-global-apps-menu nav-global-dropdown js-dropdown-menu" id="nav-global-apps-menu">
                <a href="https://www.blender.org/?utm_medium=nav-global" target="_blank">
                  <h3>BLENDER.ORG</h3>
                </a>
                <ul>
                  <li>
                    <a href="https://www.blender.org/download/?utm_medium=nav-global" target="_blank">
                      <figure>
                        <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                          <path d="m 49.15424,599.52895 a 50.360431,50.360431 0 0 0 -49.16137168,50.36043 v 200.24266 c 0,81.53594 68.34629768,149.88226 149.88223168,149.88226 h 700.2498 c 81.53593,0 149.8822,-68.34632 149.8822,-149.88226 V 649.88938 a 50.360431,50.360431 0 1 0 -100.72083,0 v 200.24266 c 0,27.57834 -21.58304,49.16138 -49.16137,49.16138 H 149.8751 c -27.57833,0 -49.16137,-21.58304 -49.16137,-49.16138 V 649.88938 A 50.360431,50.360431 0 0 0 49.15424,599.52895 Z M 249.3969,350.12491 a 50.360431,50.360431 0 0 0 -34.77267,85.13311 l 250.60309,249.40404 a 50.360431,50.360431 0 0 0 70.74442,0 L 785.37577,435.25802 A 50.360431,50.360431 0 1 0 714.63136,364.51361 L 500,579.14497 285.36864,364.51361 A 50.360431,50.360431 0 0 0 249.3969,350.12491 Z M 498.80094,0 A 50.360431,50.360431 0 0 0 449.63957,50.360432 V 649.88938 a 50.360431,50.360431 0 1 0 100.72086,0 V 50.360432 A 50.360431,50.360431 0 0 0 498.80094,0 Z" style="stroke-width:1.19906"></path>
                        </svg>
                      </figure>
                      <div>
                        <h4>Download</h4>
                        <p>Get the latest Blender, older versions, or experimental builds.</p>
                      </div>
                    </a>
                  </li>
                  <li>
                    <a href="https://www.blender.org/download/releases/?utm_medium=nav-global" target="_blank">
                      <div>
                        <h4>What&apos;s New</h4>
                        <p>Stay up-to-date with the new features in the latest Blender releases.</p>
                      </div>
                    </a>
                  </li>
                </ul>
                <a href="https://studio.blender.org/?utm_medium=nav-global" target="_blank">
                  <h3>LEARNING & RESOURCES</h3>
                </a>
                <ul>
                  <li>
                    <a href="https://studio.blender.org/?utm_medium=nav-global" target="_blank">
                      <figure>
                        <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                          <path d="m 146.70939,1.6802353 c -78.362959,0 -143.678322,64.2057377 -143.6783209,143.6570547 -7.2533835,268.45385 0,463.93349 0,709.63356 0,79.45132 65.3153619,143.65705 143.6783209,143.65705 266.17757,0.51388 460.32009,0 709.61228,0 79.45134,0 143.67832,-64.20573 143.67832,-143.65705 0.37471,-118.45983 0,-235.03162 0,-353.72203 0.017,-0.72264 0.017,-1.4456 0,-2.16825 0.43351,-118.60776 0,-235.80643 0,-353.74328 0,-79.451317 -64.22698,-143.6570547 -143.67832,-143.6570547 -241.21275,-1.18614431 -498.91438,-0.041532 -709.61228,0 z m 0,90.3436617 h 82.71228 V 228.07083 H 93.374735 v -82.73354 c 0,-30.47448 22.860165,-53.313393 53.334655,-53.313393 z m 173.05594,0 h 363.5004 c -5.81542,127.740813 0,236.658243 0,362.416273 h -363.5004 c 0.39671,-121.62159 0,-241.06277 0,-362.416273 z m 453.84406,0 h 82.71228 c 30.4745,0 53.33466,22.838913 53.33466,53.313393 v 82.73354 H 773.60939 Z M 93.374735,318.39324 H 229.42167 V 454.44017 H 93.374735 Z m 680.234655,0 H 909.65633 V 454.44017 H 773.60939 Z M 93.374735,545.86796 H 229.42167 V 681.91489 H 93.374735 Z m 226.390595,0 h 363.5004 c -5.81534,127.74773 0,236.67164 0,362.43753 h -363.5004 c 0.3967,-121.62867 0,-241.07685 0,-362.43753 z m 453.84406,0 H 909.65633 V 681.91489 H 773.60939 Z M 93.374735,772.25856 H 229.42167 v 136.04693 h -82.71228 c -30.47449,0 -53.334655,-22.86016 -53.334655,-53.33464 z m 680.234655,0 h 136.04694 v 82.71229 c 0,30.47448 -22.86016,53.33464 -53.33466,53.33464 h -82.71228 z" style="stroke-width:1.08838"></path>
                        </svg>
                      </figure>
                      <div>
                        <h4>Blender Studio</h4>
                        <p>Access production assets and knowledge from the open movies.</p>
                      </div>
                    </a>
                  </li>
                  <li>
                    <a href="https://docs.blender.org/manual/en/latest/?utm_medium=nav-global" target="_blank">
                      <div>
                        <h4>Manual</h4>
                        <p>Documentation on the usage and features in Blender.</p>
                      </div>
                    </a>
                  </li>
                </ul>
                <a href="https://projects.blender.org/?utm_medium=nav-global" target="_blank">
                  <h3>DEVELOPMENT</h3>
                </a>
                <ul>
                  <li>
                    <a href="https://code.blender.org/?utm_medium=nav-global" target="_blank">
                      <figure>
                        <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                          <path d="m 683.36434,818.19976 a 45.841084,45.841084 0 0 1 -33.83509,-13.09745 45.841084,45.841084 0 0 1 0,-64.39581 L 890.74067,499.49508 649.52925,259.37512 a 45.841084,45.841084 0 0 1 0,-64.39582 45.841084,45.841084 0 0 1 64.39581,0 l 272.8636,272.8636 a 45.841084,45.841084 0 0 1 0,64.39581 l -272.8636,272.8636 a 45.841084,45.841084 0 0 1 -30.56072,13.09745 z m -363.45431,0 A 45.841084,45.841084 0 0 1 286.07494,805.10231 L 13.211339,532.23871 a 45.841084,45.841084 0 0 1 0,-64.39581 L 286.07494,194.9793 a 45.841084,45.841084 0 0 1 64.39581,0 45.841084,45.841084 0 0 1 0,64.39582 L 109.25933,499.49508 350.47075,740.7065 a 45.841084,45.841084 0 0 1 0,64.39581 45.841084,45.841084 0 0 1 -30.56072,13.09745 z" style="stroke-width:1.09145"></path>
                        </svg>
                      </figure>
                      <div>
                        <h4>Developers Blog</h4>
                        <p>Latest development updates, by Blender developers.</p>
                      </div>
                    </a>
                  </li>
                  <li>
                    <a href="https://wiki.blender.org/?utm_medium=nav-global" target="_blank">
                      <div>
                        <h4>Documentation</h4>
                        <p>Guidelines, release notes and development docs.</p>
                      </div>
                    </a>
                  </li>
                </ul>
                <ul>
                  <li>
                    <a href="https://opendata.blender.org/?utm_medium=nav-global" target="_blank">
                      <figure>
                        <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                          <path d="M 499.99424,0 A 55.30474,55.30474 0 0 0 444.6895,55.30474 V 944.69526 A 55.30474,55.30474 0 0 0 499.99424,1000 55.30474,55.30474 0 0 0 555.29898,944.69526 V 55.30474 A 55.30474,55.30474 0 0 0 499.99424,0 Z m 332.95711,332.95711 a 55.30474,55.30474 0 0 0 -55.30474,56.43341 V 944.69526 A 55.30474,55.30474 0 0 0 832.95135,1000 55.30474,55.30474 0 0 0 888.25609,944.69526 V 389.39052 A 55.30474,55.30474 0 0 0 832.95135,332.95711 Z M 167.03713,555.30474 a 55.30474,55.30474 0 0 0 -55.30474,55.30474 V 944.69526 A 55.30474,55.30474 0 0 0 167.03713,1000 55.30474,55.30474 0 0 0 222.34187,944.69526 V 610.60948 a 55.30474,55.30474 0 0 0 -55.30474,-55.30474 z" style="stroke-width:1.12867"></path>
                        </svg>
                      </figure>
                      <div>
                        <h4>Benchmark</h4>
                        <p>A platform to collect and share results of the Blender Benchmark.</p>
                      </div>
                    </a>
                  </li>
                  <li>
                    <a href="https://conference.blender.org/?utm_medium=nav-global" target="_blank">
                      <div>
                        <h4>Blender Conference</h4>
                        <p>The yearly event that brings the community together.</p>
                      </div>
                    </a>
                  </li>
                </ul>
                <div class="nav-global-apps-menu-section-donate">
                  <a href="https://fund.blender.org/?utm_medium=nav-global" target="_blank">
                    <h3>DONATE</h3>
                  </a>
                  <ul>
                    <li>
                      <a href="https://fund.blender.org/?utm_medium=nav-global" target="_blank">
                        <figure>
                          <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                            <path d="M 273.67169,58.416076 C 201.59785,62.59427 135.79129,94.975269 86.697523,145.11359 37.603742,194.20736 4.1781939,260.01391 0,332.08775 -4.1781926,403.11704 22.980065,480.41362 86.697523,545.17562 l 45.960127,45.96013 339.47823,338.43367 a 43.871033,43.871033 0 0 0 61.62835,0 L 872.1979,591.13575 918.15804,545.17562 c 109.67766,-110.72213 109.67766,-290.38445 0,-400.06203 -110.72213,-110.722127 -290.38445,-110.722127 -400.06204,0 l -15.66822,14.62368 -15.66822,-14.62368 C 423.04211,80.351592 345.74553,53.193334 273.67169,58.416076 Z m 5.22274,86.697514 c 48.04922,-3.13365 98.18754,12.53458 146.23677,60.5838 l 47.00468,47.00468 a 43.871033,43.871033 0 0 0 61.62835,0 l 45.96013,-47.00468 c 76.25204,-76.25203 199.50874,-76.25203 276.80532,0 77.29658,77.29658 77.29658,200.5533 0,277.84988 L 810.56956,529.50739 502.42778,837.64917 194.286,529.50739 148.32588,483.54727 C 100.27665,434.45349 84.608431,384.31516 86.697523,336.26594 c 3.133646,-47.00467 26.113717,-95.0539 61.628357,-130.56855 35.51464,-35.51464 82.51932,-58.49471 130.56855,-60.5838 z" style="stroke-width:1.04455"></path>
                          </svg>
                        </figure>
                        <div>
                          <h4>Development Fund</h4>
                          <p>Support core development with a monthly contribution.</p>
                        </div>
                      </a>
                    </li>
                    <li>
                      <a href="https://www.blender.org/about/donations/?utm_medium=nav-global" target="_blank">
                        <div>
                          <h4>One-time Donations</h4>
                          <p>Perform a single donation with more payment options available.</p>
                        </div>
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isDropdownVisible: false,
      dropdownToggles: document.getElementsByClassName("js-nav-global-dropdown-toggle"),
      btnActiveClass: 'nav-global-btn-active',
      isVisibleClass: 'is-visible'
    };
  },
  methods: {
    toggleDropdown(dropdownId) {
      const el = document.getElementById(dropdownId);

      if (el) {
        if (el.classList.contains(this.isVisibleClass)) {
          this.hideAllDropdowns();
        } else {
          this.showDropdown(el);
        }
      }
    },
    hideAllDropdowns() {
      const dropdownMenus = document.getElementsByClassName("js-nav-global-dropdown");

      if (dropdownMenus) {
        for (let i = 0; i < dropdownMenus.length; i++) {
          dropdownMenus[i].classList.remove(this.isVisibleClass);
        }
      }

      this.removeActiveStyling();
    },
    showDropdown(el) {
      this.hideAllDropdowns();
      el.classList.add(this.isVisibleClass);
      this.addActiveStyling();
    },
    removeActiveStyling() {
      for (let i = 0; i < this.dropdownToggles.length; i++) {
        this.dropdownToggles[i].classList.remove(this.btnActiveClass);
      }
    },
    addActiveStyling() {
      for (let i = 0; i < this.dropdownToggles.length; i++) {
        this.dropdownToggles[i].classList.add(this.btnActiveClass);
      }
    }
  },
  mounted() {
    for (let i = 0; i < this.dropdownToggles.length; i++) {
      this.dropdownToggles[i].addEventListener("click", (e) => {
        e.stopPropagation();
        const dropdownId = this.dropdownToggles[i].getAttribute('data-dropdown-id');
        const el = document.getElementById(dropdownId);
        if (el) {
          if (el.classList.contains(this.isVisibleClass)) {
            this.hideAllDropdowns();
          } else {
            this.showDropdown(el);
          }
        }
      });
    }

    document.body.addEventListener("click", (e) => {
      if (!e.target.classList.contains("js-nav-global-dropdown")) {
        this.hideAllDropdowns();
      }
    });

    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.hideAllDropdowns();
      }
    });

    // Cleanup VPNav Vitepress attributes to make links work
    var VPNav = document.querySelector('.VPNav');
    VPNav.removeAttribute('data-v-14f22a90');
    VPNav.removeAttribute('data-v-702a693e');

    // Make header position fixed if page has sidebar
    // TODO: change to Vue route change
    setInterval(function() {
      var VPContent = document.querySelector('.VPContent');

      if (VPContent.classList.contains('has-sidebar')) {
        VPNav.classList.add('VPNav-fixed');
      } else {
        VPNav.classList.remove('VPNav-fixed');
      }
    }, 1000);
  }
};
</script>

<style>
/* This style block should contain a copy of _navigation_global.scss.
 * Custom styling for this website should be inside a <style> block right after. */
</style>

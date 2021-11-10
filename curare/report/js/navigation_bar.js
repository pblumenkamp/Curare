Vue.component('navigation-bar', {
    props: ['modulesPath', 'mainHtml'],
    data: () => ({
        navigation: Curare.navigation,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analysis']
    }),
    computed: {
        navigation_elements: function () {
            let vue = this
            let nav = {}
            for (let step of Object.keys(vue.navigation)) {
                nav[step] = []
                for (let module of vue.navigation[step]) {
                    let html = module.html_name !== null ? module.html_name : ""
                    if (html) {
                        nav[step].push({'name': module.title, 'html_name': html, new_tab: module.new_tab})
                    }
                }
                nav[step].sort((a, b) => {
                    const nameA = a.name.toUpperCase()
                    const nameB = b.name.toUpperCase()
                    if (nameA > nameB) {
                        return 1
                    } else if (nameA < nameB) {
                        return -1
                    } else {
                        return 0
                    }
                })
            }
            return nav
        },
        child_has_html: function () {
            let vue = this
            let nav = {}
            for (let step of Object.keys(vue.navigation)) {
                let has_html = false
                for (let module of vue.navigation[step]) {
                    if (module.html_name !== null) {
                        has_html = true
                        break
                    }
                }
                nav[step] = has_html
            }
            return nav
        }
    },
    template: `
        <div id="navigation-bar" class="container">
        <nav class="navbar is-fixed-top" role="navigation" aria-label="main navigation">
          <div class="navbar-menu">
            <div class="navbar-start">
              <div class="navbar-item has-dropdown is-hoverable">
                <a class="navbar-link" :href="mainHtml">
                  Overview
                </a>
    
                <div class="navbar-dropdown">
                  <a :href="mainHtml + '#summary'" class="navbar-item">
                    Curare Summary
                  </a>
                  <a :href="mainHtml + '#groups'" class="navbar-item">
                    Groups
                  </a>
                  <a :href="mainHtml + '#tools-used'" class="navbar-item">
                    Tools Used
                  </a>
                </div>
              </div>
    
              <div
                v-for="step of analysis_steps"
                v-if="step in navigation_elements & child_has_html[step]"
                class="navbar-item has-dropdown is-hoverable"
              >
                <a class="navbar-link">
                  {{ step.charAt(0).toUpperCase() + step.slice(1) }}
                </a>
    
                <div class="navbar-dropdown">
                  <template v-for="module of navigation_elements[step]">
                    <a
                      v-if="module.new_tab"
                      :href="modulesPath + module.html_name"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="navbar-item"
                      style="display: flex; align-items: center"
                    >
                      <span style="padding-right: 0.5rem">{{ module.name }}</span>
                      <i class="fas fa-external-link-alt fa-sm"></i>
                    </a>
                    <a
                      v-else
                      :href="modulesPath + module.html_name"
                      class="navbar-item"
                    >
                      {{ module.name }}
                    </a>
                  </template>
                </div>
              </div>
            </div>
            <div class="navbar-end">
              <div class="navbar-item is-hoverable" style="padding-right: 0.5rem">
                  <a href="https://github.com/pblumenkamp/curare"><i class="fab fa-github" style="font-size: 2rem"></i></a>
              </div>
              <div class="navbar-item is-hoverable" style="padding-right: 2rem">
                  <a :href="modulesPath + 'about.html'"><i class="fas fa-info-circle" style="font-size: 2rem"></i></a>
              </div>
            </div>
          </div>
        </nav>
      </div>
    `
})

new Vue({
    el: '#navigation'
})

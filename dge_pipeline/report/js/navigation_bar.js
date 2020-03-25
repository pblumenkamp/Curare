'use strict';

new Vue({
    el: '#navigation-bar',
    data: {
        navigation: Curare.navigation,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analyses'],
    },
    computed: {
        navigation_elements: function () {
            let vue = this
            let nav = {}
            for (let step of Object.keys(vue.navigation)) {
                nav[step] = []
                for (let module of vue.navigation[step]) {
                    let name = module.name.replace("_", " ").split(' ').map(function (word) {
                                 return word.charAt(0).toUpperCase() + word.slice(1)
                                 }).join(' ')
                    let html = module.html_name !== null ? module.html_name  : ""
                    nav[step].push({'name': name, 'html_name': html})
                }
                nav[step].sort(function (a,b) {
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
    }
});
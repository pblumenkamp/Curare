'use strict';

const menuItem = {
    template: '<div class="menu-item">\n        <p class="menu-label">{{step}}</p>\n        <ul class="menu-list">\n            <li v-for="module in data[step].modules">\n                <a :href="\'#\' + module.name">{{module.name}}</a>\n            </li>\n        </ul>\n    </div>',
    props: ['step', 'data']
};

new Vue({
    el: '#curare-report',
    data: {
        versionsData: Curare.versions,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analyses'],
        showAllDependencies: {
            'preprocessing': {},
            'premapping': {},
            'mapping': {},
            'analyses': {}
        }
    },
    computed: {
        steps: function steps() {
            let vue = this;

            let steps = {}
            this.analysis_steps.forEach(function (step) {
                steps[step] = vue.versionsData.filter(function (tool) {
                    return tool.step === step;
                });
            });

            return steps;
        }
    },
    components: {
        'menu-item': menuItem
    },
    methods: {
        switchVisibility: function (step, module) {
            let vue = this;
            vue.$set(vue.showAllDependencies[step], module, !vue.showAllDependencies[step][module]);
        }
    },
    created: function () {
        let vue = this;
        for (let [step, modules] of Object.entries(vue.steps)) {
            for (let module of Object.values(modules)) {
                vue.$set(vue.showAllDependencies[step], module.name, false);
            }
        }
    }
});
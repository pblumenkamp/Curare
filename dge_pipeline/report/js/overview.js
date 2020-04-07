'use strict';

new Vue({
    el: '#overview',
    data: {
        versionsData: Curare.versions,
        curare_summary: Curare.summary,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analyses'],
        showAllDependencies: {
            'preprocessing': {},
            'premapping': {},
            'mapping': {},
            'analyses': {}
        }
    },
    computed: {
        versionsTable: function () {
            let vue = this;

            let steps = {}
            this.analysis_steps.forEach(function (step) {
                steps[step] = vue.versionsData.filter(function (tool) {
                    return tool.step === step;
                });
            });

            return steps;
        },
        curare_execution_date: function () {
            let vue = this;
            //let date = new Date(vue.curare_summary.date);
            //return date.toString();
            return vue.curare_summary.date
        },
        curare_runtime: function () {
            let vue = this;
            if (vue.curare_summary.runtime > 3600) { // runtime longer than 1 hour
                return `${(vue.curare_summary.runtime / 3600).toFixed(1)} h`
            } else {
                return `${(vue.curare_summary.runtime / 60).toFixed(1)} min`
            }
        },
        groups_header: function () {
            let vue = this;
            return vue.curare_summary.groups[0].map(function (header) {
                return header.replace("_", " ").split(' ').map(function (word) {
                    return word.charAt(0).toUpperCase() + word.slice(1)
                }).join(' ')
            })
        },
        groups_body: function () {
            let vue = this;
            return vue.curare_summary.groups.slice(1)
        }
    },
    methods: {
        switchVisibility: function (step, module) {
            let vue = this;
            vue.$set(vue.showAllDependencies[step], module, !vue.showAllDependencies[step][module]);
        }
    },
    created: function () {
        let vue = this;
        for (let [step, modules] of Object.entries(vue.versionsTable)) {
            for (let module of Object.values(modules)) {
                vue.$set(vue.showAllDependencies[step], module.name, false);
            }
        }
    }
});
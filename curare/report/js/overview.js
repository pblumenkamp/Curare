'use strict';

new Vue({
    el: '#overview',
    data: {
        versionsData: Curare.versions,
        curare_summary: Curare.summary,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analysis'],
        currentPage: 1,
        showAllDependencies: {
            'preprocessing': {},
            'premapping': {},
            'mapping': {},
            'analysis': {}
        },
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
            let total_seconds = Math.floor(vue.curare_summary.runtime)
            if (total_seconds >= 3600) { // runtime longer than 1 hour
                let hours = Math.floor(total_seconds / 3600)
                let minutes = Math.floor((total_seconds % 3600) / 60)
                let hours_label = (hours === 1) ? "hour" : "hours"
                let minutes_label = (minutes === 1) ? "minute" : "minutes"
                return `${hours} ${hours_label} ${minutes} ${minutes_label}`
            } else if (total_seconds >= 60) {
                let minutes = Math.floor(total_seconds / 60)
                let seconds = total_seconds % 60
                let minutes_label = (minutes === 1) ? "minute" : "minutes"
                let seconds_label = (seconds === 1) ? "second" : "seconds"
                return `${minutes} ${minutes_label} ${seconds} ${seconds_label}`
            } else {
                let seconds_label = (total_seconds === 1) ? "second" : "seconds"
                return `${total_seconds} ${seconds_label}`
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
        groups_column: function () {
            let vue = this;
            return vue.curare_summary.groups[0].map(function (header) {
                var element = {}
                element['field'] = header
                element['label'] = header.replace("_", " ").split(' ').map(function (word) {
                                       return word.charAt(0).toUpperCase() + word.slice(1)
                                   }).join(' ')
                return element
            })
        },
        groups_body: function () {
            let vue = this;
            return vue.curare_summary.groups.slice(1)
        },
        groups_data: function () {
            let vue = this;
            let header = vue.curare_summary.groups[0]
            return vue.curare_summary.groups.slice(1).map(function (line) {
                let row = {}
                for (var i=0; i<line.length; i++) {
                    row[header[i]] = line[i]
                }
                return row
            })
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

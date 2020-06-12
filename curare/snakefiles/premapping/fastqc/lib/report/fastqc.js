'use strict';

new Vue({
    el: '#fastqc',
    data: {
        fastqc_reports: Curare.fastqc.reports,
        paired_end: Curare.fastqc.paired_end,
    },
    computed: {
        table_columns: function() {
            const vue = this
            if (vue.paired_end) {
                return [{
                    field: 'name',
                    label: 'Sample'
                }, {
                    field: 'forward',
                    label: 'Forward'
                },
                {
                    field: 'reverse',
                    label: 'Reverse'
                }]
            } else {
                return [{
                    field: 'name',
                    label: 'Sample'
                }, {
                    field: 'forward',
                    label: 'Report'
                }]
            }
        },
        table_data: function () {
            const vue = this
            const table = []
            for (const sample of vue.fastqc_reports) {
                let entry = {
                    name: sample.name,
                    forward: `../modules/fastqc/${sample.forward}`
                }
                if (vue.paired_end) {
                    entry['reverse'] = `../modules/fastqc/${sample.reverse}`
                }
                table.push(entry)
            }
            return table
        }
    },
    methods: {

    },
});

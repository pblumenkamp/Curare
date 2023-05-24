'use strict';

new Vue({
    el: '#fastp',
    data: {
        fastp_reports: Curare.fastp.reports,
        paired_end: Curare.fastp.paired_end,
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
            for (const sample of vue.fastp_reports) {
                let entry = {
                    name: sample.name,
                    forward: `../modules/fastp/${sample.forward}`
                }
                if (vue.paired_end) {
                    entry['reverse'] = `../modules/fastp/${sample.reverse}`
                }
                table.push(entry)
            }
            return table
        },
        
    },
    methods: {

    },
});

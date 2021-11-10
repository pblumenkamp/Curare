'use strict';

new Vue({
    el: '#bwa',
    data: {
        bwa_stats: Curare.bwa_mem.stats,
        bwa_settings: Curare.bwa_mem.settings,
        paired_end: Curare.bwa_mem.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        bwa_settings_columns: [
            {
                field: 'key',
                label: 'Key',
                visible: true
            },
            {
                field: 'value',
                label: 'Value',
                visible: true
            }
        ]
    },
    computed: {
        bwa_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "BWA Version",
                    value: vue.bwa_settings["bwa_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Additional BWA MEM Parameters",
                    value: (vue.bwa_settings["additional_mem_parameters"]) ? '"' + vue.bwa_settings["additional_mem_parameters"] + '"' : "-"
                }
            ]
            return settings
        }
    },
    methods: {}
});

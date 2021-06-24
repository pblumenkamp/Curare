'use strict';

new Vue({
    el: '#bowtie2',
    data: {
        bowtie2_stats: Curare.bowtie2.stats,
        paired_end: Curare.bowtie2.paired_end,
        bowtie2_settings: Curare.bowtie2.settings,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        bw2_settings_columns: [
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
        bw2_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "Bowtie2 Version",
                    value: vue.bowtie2_settings["bowtie2_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Used Bowtie2 Preset",
                    value: '"' + vue.bowtie2_settings["used_mapping_preset"] + '"'
                },
                {
                    key: "Used Shared-Memory Mode (-mm)",
                    value: (vue.bowtie2_settings["use_shared_memory"] === "true") ? "True" : "False"
                },
                {
                    key: "Additional Bowtie2 Parameters",
                    value: (vue.bowtie2_settings["additional_parameters"]) ? '"' + vue.bowtie2_settings["additional_parameters"] + '"' : "-"
                }
            ]
            return settings
        }
    },
    methods: {}
});

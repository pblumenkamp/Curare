'use strict';

new Vue({
    el: '#segemehl',
    data: {
        segemehl_stats: Curare.segemehl.stats,
        segemehl_settings: Curare.segemehl.settings,
        paired_end: Curare.segemehl.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: [],
        segemehl_settings_columns: [
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
        segemehl_settings_data: function() {
            let vue = this
            let settings = [
                {
                    key: "Segemehl Version",
                    value: vue.segemehl_settings["segemehl_version"] 
                },
                {
                    key: "Sequencing Strategy",
                    value: (vue.paired_end) ? "Paired-End" : "Single-End"
                },
                {
                    key: "Segemehl Accuracy (in percent)",
                    value: (vue.segemehl_settings["segemehl_accuracy"]) ? '"' + vue.segemehl_settings["segemehl_accuracy"] + '"' : "-"
                },
                {
                    key: "Additional Segemehl Parameters",
                    value: (vue.segemehl_settings["additional_segemehl_parameters"]) ? '"' + vue.segemehl_settings["additional_segemehl_parameters"] + '"' : "-"
                }
            ]
            return settings
        }
    },
    methods: {}
});

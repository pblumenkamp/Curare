'use strict';

new Vue({
    el: '#bwa',
    data: {
        bwa_stats: Curare.bwa_sw.stats,
        paired_end: Curare.bwa_sw.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: []
    },
    computed: {},
    methods: {}
});
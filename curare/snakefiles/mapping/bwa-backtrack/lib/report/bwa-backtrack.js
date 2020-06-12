'use strict';

new Vue({
    el: '#bwa',
    data: {
        bwa_stats: Curare.bwa_backtrack.stats,
        paired_end: Curare.bwa_backtrack.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: []
    },
    computed: {},
    methods: {}
});

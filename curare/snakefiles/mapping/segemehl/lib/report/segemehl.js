'use strict';

new Vue({
    el: '#segemehl',
    data: {
        segemehl_stats: Curare.segemehl.stats,
        paired_end: Curare.segemehl.paired_end,
        stats_percent_header_paired_end: ["", ""],
        stats_in_percent: []
    },
    computed: {},
    methods: {}
});

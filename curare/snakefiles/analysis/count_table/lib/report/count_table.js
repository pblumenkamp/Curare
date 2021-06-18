'use strict';

new Vue({
    el: '#counttable',
    data: {
        counttable_stats: Curare.count_table.stats,
        paired_end: Curare.count_table.paired_end,
        stats_in_percent: false,
        chart: undefined,
        currentPage: 1,
        stats_columns: [
            {
                field: 'name',
                label: 'Sample',
                visible: true
            },
            {
                field: 'reads',
                label: 'Total Reads',
                visible: true,
                numeric: true
            },
            {
                field: 'Assigned',
                label: 'Assigned',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Unmapped',
                label: 'Unassigned Unmapped',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Read_Type',
                label: 'Unassigned Read Type',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Singleton',
                label: 'Unassigned Singleton',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_MappingQuality',
                label: 'Unassigned MappingQuality',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Chimera',
                label: 'Unassigned Chimera',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_FragmentLength',
                label: 'Unassigned FragmentLength',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Duplicate',
                label: 'Unassigned Duplicate',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_MultiMapping',
                label: 'Unassigned MultiMapping',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Secondary',
                label: 'Unassigned Secondary',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_NonSplit',
                label: 'Unassigned NonSplit',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_NoFeatures',
                label: 'Unassigned NoFeatures',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Overlapping_Length',
                label: 'Unassigned Overlapping_Length',
                visible: true,
                numeric: true
            },
            {
                field: 'Unassigned_Ambiguity',
                label: 'Unassigned Ambiguity',
                visible: true,
                numeric: true
            }
        ]
    },
    computed: {
        reads_per_sample: function () {
            const vue = this
            const sums = []
            for (const row of vue.counttable_stats) {
                let sum = 0
                for (const [key, value] of Object.entries(row)) {
                    if (key !== 'name') {
                        sum += parseFloat(value)
                    }
                }
                sums.push(sum)
            }
            return sums
        },
        stats_table: function () {
            const vue = this
            if (vue.stats_in_percent) {
                return vue.stats_table_relative
            } else {
                return vue.stats_table_absolute
            }
        },
        stats_table_absolute: function () {
            const vue = this
            const data = vue.counttable_stats
            for (const [i, row] of data.entries()) {
                row['reads'] = vue.reads_per_sample[i]
            }
            for (const col of vue.stats_columns) {
                let all_zero = true
                for (const row of data) {
                    if (row[col['field']] !== '0') {
                        all_zero = false
                        break
                    }
                }
                if (all_zero) {
                    col['visible'] = false
                }
            }
            return data
        },
        stats_table_relative: function () {
            const vue = this
            const data = vue.stats_table_absolute
            const table = []
            for (const row of data) {
                const new_row = {}
                for (const [key, value] of Object.entries(row)) {
                    if (['name', 'reads'].includes(key)) {
                        new_row[key] = value
                    } else {
                        new_row[key] = ((parseFloat(value) / parseFloat(row['reads'])) * 100).toFixed(2)
                    }
                }
                table.push(new_row)
            }
            return table
        }
    },
    methods: {
        createChart(chartId, type, data, options) {
            const vue = this
            const ctx = document.getElementById(chartId);
            if (vue.chart !== undefined) {
                vue.chart.destroy()
            }
            const myChart = new Chart(ctx, {
                type: type,
                data: data,
                options: options,
            });
            vue.chart = myChart
        },
        create_stacked_bar_chart() {
            const vue = this
            const colors = [
                'rgba(0,160,250,1)',
                'rgba(10,155,75,1)',
                'rgba(255,130,95,1)',
                'rgba(250,120,250,1)',
                'rgba(160,250,130,1)',
                'rgba(170,10,60,1)',
                'rgba(0,110,130,1)',
                'rgba(234,214,68,1)',
                'rgba(130,20,160,1)',
                'rgba(20,210,220,1)',
                'rgba(0,90,200,1)',
                'rgba(250,230,130,1)',
                'rgba(0,0,0,1)',
                'rgba(125,125,125,1)'
            ]
            const datasets = []

            for (const [i, category] of vue.stats_columns.entries()) {
                if (!['name', 'reads'].includes(category.field) && category.visible) {
                    const data = []
                    for (const row of vue.stats_table) {
                        data.push(row[category.field])
                    }
                    const color = colors[i-2]  // 'name' and 'reads' don't need any color
                    datasets.push({
                        label: category.label,
                        data: data,
                        backgroundColor: data.map((x) => color),
                        borderColor: data.map((x) => color),
                        borderWidth: 2
                    })
                }
            }

            var options = {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }

            if (vue.stats_in_percent) {
                options.scales.y.max = 100
            }

            const chartID = 'stacked_barchart'
            this.createChart(
                chartID,
                'bar',
                {
                    datasets: datasets,
                    labels: vue.stats_table.map((x) => x['name']),
                },
                options
            )
        },
    },
    watch: {
      stats_in_percent: function () {
          this.create_stacked_bar_chart()
      }
    },
    mounted: function () {
        const vue = this
        this.$nextTick(function () {
            this.create_stacked_bar_chart()
        })
    }
});

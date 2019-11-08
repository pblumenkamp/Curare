const menuItem = {
    template:
    `<div class="menu-item">
        <p class="menu-label">{{step}}</p>
        <ul class="menu-list">
            <li v-for="module in data[step].modules">
                <a :href="'#' + module.name">{{module.name}}</a>
            </li>
        </ul>
    </div>`,
    props: ['step', 'data']
}

new Vue({
    el: '#curare-report',
    data: {
        reportData: Seed.reportData,
        analysis_steps: [
            'preprocessing',
            'premapping',
            'mapping',
            'analyses'
        ]
    },
    computed: {
        steps() {
            let steps = {}
            this.analysis_steps.forEach(step => {
                steps[step] = this.reportData.overview.toolsUsed.filter(tool => tool.step === step)
            })

            return steps
        },
        tableColumns() {
            return Object.keys(this.reportData.mapping.stats)
        }
    },
    components: {
        'menu-item': menuItem
    },
    methods: {
        showAll: function(event) {
            const selector = event.target.className.split('show-all-')[1]
            const list = document.getElementById(selector)
            for (let item of list.getElementsByClassName('hideable')) {
                item.classList.toggle('is-hidden')
            }
        }
    }
});
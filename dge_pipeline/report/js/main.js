'use strict';

var menuItem = {
    template: '<div class="menu-item">\n        <p class="menu-label">{{step}}</p>\n        <ul class="menu-list">\n            <li v-for="module in data[step].modules">\n                <a :href="\'#\' + module.name">{{module.name}}</a>\n            </li>\n        </ul>\n    </div>',
    props: ['step', 'data']
};

new Vue({
    el: '#curare-report',
    data: {
        reportData: Seed.reportData,
        analysis_steps: ['preprocessing', 'premapping', 'mapping', 'analyses']
    },
    computed: {
        steps: function steps() {
            var _this = this;

            var steps = {};
            this.analysis_steps.forEach(function (step) {
                steps[step] = _this.reportData.overview.toolsUsed.filter(function (tool) {
                    return tool.step === step;
                });
            });

            return steps;
        },
        tableColumns: function tableColumns() {
            return Object.keys(this.reportData.mapping.stats);
        }
    },
    components: {
        'menu-item': menuItem
    },
    methods: {
        showAll: function showAll(event) {
            var selector = event.target.className.split('show-all-')[1];
            var list = document.getElementById(selector);
            var _iteratorNormalCompletion = true;
            var _didIteratorError = false;
            var _iteratorError = undefined;

            try {
                for (var _iterator = list.getElementsByClassName('hideable')[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                    var item = _step.value;

                    item.classList.toggle('is-hidden');
                }
            } catch (err) {
                _didIteratorError = true;
                _iteratorError = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion && _iterator.return) {
                        _iterator.return();
                    }
                } finally {
                    if (_didIteratorError) {
                        throw _iteratorError;
                    }
                }
            }
        }
    }
});
Vue.component('curare-footer', {
    props: ['imgPath'],
    data: () => ({}),
    computed: {},
    template: `
    <div class="content">
      <div style="display: flex; align-items: center; justify-content: center">
        <p><strong>CURARE</strong> by <a href="mailto:patrick.blumenkamp@computational.bio.uni-giessen.de">Patrick Blumenkamp</a>.</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: center; margin-top: 2rem">
        <p>Created with:</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: center; margin-top: 0.5rem;">
        <a href="http://bulma.io">
          <img :src="imgPath + '/bulma.png'" alt="made with Bulma" style="height: 32px; width: auto; padding: 0 0.6rem 0 0">
        </a>
        <a href="https://buefy.org/">
          <img :src="imgPath + '/buefy-logo.png'" alt="Buefy Logo" style="height: 32px; width: auto; padding: 0 0.6rem 0 0.6rem">
        </a>
        <a href="http://chartjs.org">
          <img :src="imgPath + '/chartjs.svg'" alt="Chart.js" style="height: 72px; width: auto; padding: 0 0.6rem 0 0.6rem">
        </a>
        <a href="http://vuejs.org">
          <img :src="imgPath + '/vuejs.png'" alt="Vue.js" style="height: 64px; width: auto; padding: 0 0.6rem 0 0">
        </a>
      </div>
    </div>
    `
})

new Vue({
    el: '#footer'
})

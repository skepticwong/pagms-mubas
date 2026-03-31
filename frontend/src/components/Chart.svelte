<script>
  import { onMount, onDestroy } from "svelte";
  import ApexCharts from "apexcharts";

  export let options = {};

  let chartElement;
  let chart;

  onMount(() => {
    chart = new ApexCharts(chartElement, options);
    chart.render();
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });

  $: if (chart && options) {
    chart.updateOptions(options, false, true); // Don't redraw paths, animate
  }
</script>

<div bind:this={chartElement} class="w-full h-full"></div>

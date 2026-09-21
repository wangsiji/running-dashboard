/* 表现层：读 window.RUN_DATA（pipeline 标准化 schema），渲染全部图表。
 * 加新图 = 加一个 div + 一个 echarts.init 配置。不碰数据来源。
 */
(function () {
  var D = window.RUN_DATA || { days: [], stats: {}, geo: [] };
  var days = D.days || [];
  var dates = days.map(function (d) { return d.date; }).filter(Boolean);

  var AX = {
    type: 'category', data: dates,
    axisLine: { lineStyle: { color: '#24314d' } },
    axisLabel: { color: '#8fa0bd', fontSize: 11 }
  };
  var AY = {
    type: 'value',
    splitLine: { lineStyle: { color: '#182337' } },
    axisLabel: { color: '#8fa0bd', fontSize: 11 }
  };
  var tooltipAxis = { trigger: 'axis' };

  function init(id) { return echarts.init(document.getElementById(id)); }

  /* —— 图1：累计距离（柱=单日，线=累计） —— */
  (function () {
    var ch = init('c-dist');
    var km = days.map(function (d) { return d.dist_km || 0; });
    var cum = [], t = 0;
    km.forEach(function (k) { t += k; cum.push(+t.toFixed(1)); });
    ch.setOption({
      tooltip: tooltipAxis,
      xAxis: AX, yAxis: AY,
      series: [
        { type: 'bar', data: km, itemStyle: { color: '#38bdf8', borderRadius: [3, 3, 0, 0] } },
        { type: 'line', data: cum, smooth: true, symbol: 'none',
          lineStyle: { color: '#f472b6', width: 2 },
          label: { show: true, position: 'top', color: '#f472b6', fontSize: 10 } }
      ]
    });
  })();

  /* —— 折2：配速趋势 —— */
  (function () {
    var ch = init('c-pace');
    var p = days.filter(function (d) { return d.pace != null; }).map(function (d) { return [d.date, +d.pace.toFixed(2)]; });
    ch.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: AX, yAxis: Object.assign({}, AY, { name: '分/公里', inverse: true }),
      series: [{ type: 'line', data: p, smooth: true, symbol: 'none',
                 lineStyle: { color: '#38bdf8', width: 2 } }]
    });
  })();

  /* —— 折3：心率 —— */
  (function () {
    var ch = init('c-hr');
    var h = days.filter(function (d) { return d.hr != null; }).map(function (d) { return [d.date, d.hr]; return [d.date, d.hr]; });
    ch.setOption({
      tooltip: tooltipAxis,
      xAxis: AX, yAxis: Object.assign({}, AY, { min: 100 }),
      series: [{ type: 'line', data: h, smooth: true, symbol: 'none',
                 lineStyle: { color: '#fb7185', width: 2 } }]
    });
  })();

  /* —— 折4：睡眠 —— */
  (function () {
    var ch = init('c-sleep');
    var s = days.filter(function (d) { return d.bed_min; }).map(function (d) { return [d.date, d.bed_min]; });
    ch.setOption({
      tooltip: tooltipAxis,
      xAxis: AX, yAxis: Object.assign({}, AY, { name: '分钟' }),
      series: [{ type: 'bar', data: s, itemStyle: { color: '#34d399', borderRadius: [3, 3, 0, 0] } }]
    });
  })();

  /* —— 散点：地理 —— */
  (function () {
    var geo = D.geo || [];
    var ch = init('c-geo');
    ch.setOption({
      tooltip: { formatter: function (p) { return (p.data[3] || '') + '<br/>' + p.data[2]; } },
      xAxis: { type: 'value', name: '经度', axisLabel: { color: '#8fa0bd', formatter: function (v) { return v.toFixed(1); } } },
      yAxis: { type: 'value', name: '纬度', axisLabel: { color: '#8fa0bd', formatter: function (v) { return v.toFixed(2); } } },
      series: [{ type: 'scatter', symbolSize: 12, itemStyle: { color: '#38bdf8' },
                 data: geo.map(function (g) { return { value: [g.lng, g.lat], name: g.location }; }) }]
    });
  })();

  /* —— 统计卡 —— */
  (function () {
    var st = D.stats || {};
    function stat(label, val) {
      return '<div class="stat"><div class="label">' + label + '</div><div class="value"><span>' + val + '</span></div></div>';
    }
    document.getElementById('stats').innerHTML =
      stat('累计距离', (st.total_km != null ? st.total_km : '—') + ' <span class=unit>km</span>') +
      stat('跑步次数', (st.total_runs != null ? st.total_runs : 0)) +
      stat('平均配速', (st.avg_pace != null ? st.avg_pace.toFixed(2) : '—') + ' <span class=unit>分/km</span>') +
      stat('平均心率', (st.avg_hr != null ? st.avg_hr : '—') + ' <span class=unit>bpm</span>');
    document.getElementById('updated').textContent = '更新于 ' + (D.updated_at || '');
  })();
})();
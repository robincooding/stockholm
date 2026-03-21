import { useRef, useEffect } from 'react';
import Plotly from 'plotly.js-dist-min';

export default function PlotChart({ data, layout, style }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current || !data) return;
    Plotly.newPlot(ref.current, data, layout, {
      responsive: true,
      displayModeBar: false,
    });
    return () => {
      if (ref.current) Plotly.purge(ref.current);
    };
  }, [data, layout]);

  return <div ref={ref} style={style} />;
}
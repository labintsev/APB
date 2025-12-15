document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('form[action*="update_active"]');
  if (!form) return;

  // compute and update calculated values (calculated population and price)
  function computeAndUpdate() {
    try {
      const checked = Array.from(form.querySelectorAll('input[name="active"]:checked'));
      let totalPopulation = 0; // population values shown in table (millions)
      let sumSmi = 0;
      let sumRegion = 0;
      let count = 0;

      checked.forEach(cb => {
        const popAttr = cb.getAttribute('data-population');
        const smiAttr = cb.getAttribute('data-smi-rating');
        const regAttr = cb.getAttribute('data-region-rating');

        const popVal = parseFloat((popAttr || '0').toString().replace(',', '.'));
        const smiVal = parseFloat((smiAttr || '0').toString().replace(',', '.'));
        const regVal = parseFloat((regAttr || '0').toString().replace(',', '.'));

        if (!isNaN(popVal)) totalPopulation += popVal;
        if (!isNaN(smiVal)) sumSmi += smiVal;
        if (!isNaN(regVal)) sumRegion += regVal;
        count += 1;
      });

      const avgSmi = count ? (sumSmi / count) : 0;
      const avgRegion = count ? (sumRegion / count) : 0;

      // Update calculated population span (shown in millions)
      const calcSpan = document.getElementById('calculated_population_value');
      if (calcSpan) calcSpan.textContent = totalPopulation.toFixed(2);

      // Compute price: price = avg_smi * avg_region * total_population
      // Here totalPopulation is already in millions, so result is in millions
      const price = avgSmi * avgRegion * totalPopulation;
      const priceSpan = document.getElementById('price_value');
      if (priceSpan) priceSpan.textContent = price.toFixed(2);

    } catch (err) {
      console.error('Error computing sum on client:', err);
    }
  }

  // Attach change listeners to checkboxes for live updates
  const checkboxes = Array.from(form.querySelectorAll('input[name="active"]'));
  checkboxes.forEach(cb => cb.addEventListener('change', computeAndUpdate));

  // On submit: compute & update, then allow the form to submit
  form.addEventListener('submit', function (e) {
    try {
      computeAndUpdate();
    } catch (err) {
      console.error('Error before submit compute:', err);
    }
    // allow normal submit to proceed
  });
});

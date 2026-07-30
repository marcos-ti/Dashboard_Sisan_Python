// ==========================================
// PAINEL DE ADESÕES - SISAN (ULTRA RÁPIDO)
// ==========================================

function atualizarKpi(elementId, valor) {
  const container = document.getElementById(elementId);
  if (container) {
    let numero = Number(valor) || 0;
    container.innerText = numero.toLocaleString("pt-BR");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  console.log("Buscando KPIs otimizados...");

  fetch("/api/dados")
    .then((response) => {
      if (!response.ok) throw new Error("Erro na resposta do servidor.");
      return response.json();
    })
    .then((dados) => {
      if (!dados) {
        console.error("Dados vazios.");
        return;
      }

      console.log("Dados carregados instantaneamente!", dados);

      // Preenche os cards diretamente com os valores calculados pelo Python
      atualizarKpi("kpi_totais", dados.total);
      atualizarKpi("kpi_com_adesao", dados.aderidos);
      atualizarKpi("kpi_sem_adesao", dados.sem_adesao);
      atualizarKpi("kpi_em_processo", dados.em_processo);
      atualizarKpi("kpi_suspensa", dados.suspensa);
    })
    .catch((error) => {
      console.error("Erro crítico:", error);
    });
});

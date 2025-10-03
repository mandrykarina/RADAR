async function analyzeQuery() {
  const timeValue = document.getElementById("timeValue").value || "1";
  const timeUnit = document.getElementById("timeUnit").value;
  const resultDiv = document.getElementById("result");

  const query = `Выдай новости за ${timeValue} ${timeUnit}`;

  resultDiv.innerHTML = '<p class="loading">Анализируем новости...</p>';

  try {
    // Запрос к backend API (замени URL на свой FastAPI endpoint)
    const response = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await response.json();

    resultDiv.innerHTML = `
      <article class="article">
        <h2>Результат анализа</h2>
        <p>${data.article || "Не удалось сгенерировать статью."}</p>
      </article>
    `;
  } catch (error) {
    resultDiv.innerHTML = '<p class="loading">Ошибка при подключении к серверу</p>';
  }
}

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bar, Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
} from "chart.js";
import "./FeedbackPage.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement
);

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://localhost:8000/api/feedback/structured")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ Structured feedback received:", data);
        setFeedback(data);
      })
      .catch((err) => {
        console.error("❌ Error fetching feedback:", err);
        setFeedback({ error: "Error fetching feedback." });
      });
  }, []);

  const renderList = (title, items) => {
    if (!Array.isArray(items) || items.length === 0) return null;

    return (
      <div className="feedback-section">
        <h3>{title}</h3>
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  const renderCharts = (metrics) => {
    if (!metrics || typeof metrics !== "object") return null;

    const labels = Object.keys(metrics);
    const dataValues = Object.values(metrics);

    const barData = {
      labels,
      datasets: [
        {
          label: "Score by Phase",
          data: dataValues,
          backgroundColor: "rgba(54, 162, 235, 0.6)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
      ],
    };

    const radarData = {
      labels,
      datasets: [
        {
          label: "Talk evaluation",
          data: dataValues,
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 1)",
          borderWidth: 2,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: "Evaluation of the talk by section" },
      },
      scales: {
        y: {
          min: 0,
          max: 20,  // ⬅️ Máximo del eje Y
          ticks: {
            stepSize: 5
          },
          title: {
            display: true,
            text: "Puntuation (max. 20)"
          }
        }
      }
    };

    return (
      <div className="feedback-charts">
        <div className="chart-container">
          <Bar data={barData} options={options} />
        </div>
          <div className="chart-container">
            <Radar
              data={radarData}
              options={{
                responsive: true,
                plugins: {
                  legend: { position: "top" },
                  title: { display: true, text: "Evaluación de la charla (Radar)" },
                },
                scales: {
                  r: {
                    min: 0,
                    max: 20,
                    ticks: {
                      stepSize: 5,
                    },
                    pointLabels: {
                      font: {
                        size: 12,
                      },
                    },
                  },
                },
              }}
            />
          </div>
      </div>
    );
  };

  const renderOverallScore = (metrics) => {
    if (!metrics || typeof metrics !== "object") return null;
    const values = Object.values(metrics);
    if (!values.length) return null;

    const average = (
      values.reduce((acc, v) => acc + v, 0) / values.length
    ).toFixed(1);
    return (
      <div className="feedback-score">
        <h3>
          🎯 Overall note of the talk: <span>{average} / 100</span>
        </h3>
      </div>
    );
  };

  if (!feedback) return <div className="feedback-loading">Loading feedback...</div>;
  if (feedback.error) return <div className="feedback-error">{feedback.error}</div>;

  return (
    <div className="feedback-page">
      <h2>📝 Feedback Summary</h2>
      {renderOverallScore(feedback.metrics)}
      {renderCharts(feedback.metrics)}
      <div className="feedback-lists">
        {renderList("💡 Suggestions", feedback.suggestions)}
        {renderList("🐞 Issues", feedback.issues)}
      </div>
    </div>
  );
}
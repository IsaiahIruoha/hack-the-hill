import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [days, setDays] = useState({}); // Store streak data with date strings as keys
  const [isPopupVisible, setIsPopupVisible] = useState(false);

  // Helper function to get date string in 'YYYY-MM-DD' format
  const getDateString = (date) => {
    return date.toISOString().split('T')[0];
  };

  // Generate an array of the last 7 dates including today
  const getLast7Days = () => {
    const last7Days = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      last7Days.push(date);
    }
    return last7Days;
  };

  // Function to toggle popup visibility
  const togglePopup = () => {
    setIsPopupVisible(!isPopupVisible);
  };

  // Load streak data from localStorage
  useEffect(() => {
    const storedDays = JSON.parse(localStorage.getItem('streakDays')) || {};
    setDays(storedDays);
  }, []);

  // Function to mark current day as complete when simulator is launched
  const markDayAsComplete = () => {
    const todayString = getDateString(new Date());
    const updatedDays = { ...days, [todayString]: 'completed' };
    setDays(updatedDays);
    localStorage.setItem('streakDays', JSON.stringify(updatedDays));
  };

  // Function to determine if a day is active, completed, or inactive
  const getDayStatus = (dateString) => {
    const todayString = getDateString(new Date());
    if (dateString === todayString) {
      return days[dateString] === 'completed' ? 'completed' : 'active';
    } else {
      return days[dateString] === 'completed' ? 'completed' : 'inactive';
    }
  };

  // Function to calculate the current streak count
  const getStreakCount = () => {
    let streak = 0;
    let today = new Date();
    let dateString = getDateString(today);
    while (days[dateString] === 'completed') {
      streak++;
      today.setDate(today.getDate() - 1);
      dateString = getDateString(today);
    }
    return streak;
  };

  return (
    <div className="container">
      <div id="home"></div>
      <nav>
        <a className="foresights" href="https://foresights.ca" target="_blank" rel="noreferrer">
          <img src="/favicon.png" alt="foresights logo" />
        </a>
        <ul className="nav-links">
          {getLast7Days().map((date) => {
            const dateString = getDateString(date);
            const dayLabel = date.toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 2);
            const dayStatus = getDayStatus(dateString);

            return (
              <li key={dateString}>
                <span className="day-label">{dayLabel}</span>
                <div className={`day-icon ${dayStatus}`}>
                  {/* Checkmark for completed days and cross for active/inactive */}
                  {dayStatus === 'completed' ? (
                  <span className="checkmark">
                    <i className="fas fa-check"></i>  {/* FontAwesome check icon */}
                  </span>
                ) : (
                  <span className="crossmark">
                    <i className="fas fa-times"></i>  {/* FontAwesome cross icon */}
                  </span>
                )}
                </div>
              </li>
            );
          })}
        </ul>
        <div className="streak-icon-container">
          <img src="/flame.png" alt="streak icon" className="streak-icon" />
          <p className="streak-count">{getStreakCount()}</p>
        </div>
      </nav>

      <div className="content-box">
        <div className="content">
          {/* Stat boxes */}
          <div className="stats">
            <div className="stat-box">
              <h3>Swing Speed</h3>
              <p>120 mph</p>
            </div>
            <div className="stat-box">
              <h3>Ball Speed</h3>
              <p>150 mph</p>
            </div>
            <div className="stat-box">
              <h3>Vertical</h3>
              <p>15°</p>
            </div>
            <div className="stat-box">
              <h3>Horizontal</h3>
              <p>15°</p>
            </div>
          </div>
          <div className="image-placeholder">
            {/* Placeholder div for future content */}
          </div>
        </div>
      </div>

      <div>
        <a
          href="https://foresights.ca/simulator"
          className="btn btn-more"
          target="_blank"
          rel="noreferrer"
          onClick={markDayAsComplete}
        >
          Launch Simulator<i className="fas fa-chevron-right"></i>
        </a>
      </div>

      {isPopupVisible && (
        <div className="popup visible">
          <h3>Authors</h3>
          <hr />
          <a href="https://www.linkedin.com/in/isaiahiruoha/" target="_blank" rel="noreferrer">
            Isaiah Iruoha
          </a>
          <a href="https://www.linkedin.com/in/connorleung/" target="_blank" rel="noreferrer">
            Connor Leung
          </a>
          <a href="https://www.linkedin.com/in/ryan-z-su/" target="_blank" rel="noreferrer">
            Ryan Su
          </a>
        </div>
      )}
      <div className="icon-background" onClick={togglePopup}>
        <svg className={`authors ${isPopupVisible ? 'rotate' : ''}`} fill="#000000" height="800px" width="800px" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink" 
        viewBox="0 0 964.07 964.07" xmlSpace="preserve">
      <g>
        <path d="M850.662,877.56c-0.77,0.137-4.372,0.782-10.226,1.831c-230.868,41.379-273.337,48.484-278.103,49.037
          c-11.37,1.319-19.864,0.651-25.976-2.042c-3.818-1.682-5.886-3.724-6.438-4.623c0.268-1.597,2.299-5.405,3.539-7.73
          c1.207-2.263,2.574-4.826,3.772-7.558c7.945-18.13,2.386-36.521-14.51-47.999c-12.599-8.557-29.304-12.03-49.666-10.325
          c-12.155,1.019-225.218,36.738-342.253,56.437l-57.445,45.175c133.968-22.612,389.193-65.433,402.622-66.735
          c11.996-1.007,21.355,0.517,27.074,4.4c3.321,2.257,2.994,3.003,2.12,4.997c-0.656,1.497-1.599,3.264-2.596,5.135
          c-3.835,7.189-9.087,17.034-7.348,29.229c1.907,13.374,11.753,24.901,27.014,31.626c8.58,3.78,18.427,5.654,29.846,5.654
          c4.508,0,9.261-0.292,14.276-0.874c9.183-1.065,103.471-17.67,280.244-49.354c5.821-1.043,9.403-1.686,10.169-1.821
          c9.516-1.688,15.861-10.772,14.172-20.289S860.183,875.87,850.662,877.56z"/>
        <path d="M231.14,707.501L82.479,863.005c-16.373,17.127-27.906,38.294-33.419,61.338l211.087-166.001
          c66.081,29.303,118.866,38.637,159.32,38.637c71.073,0,104.065-28.826,104.065-28.826c-66.164-34.43-75.592-98.686-75.592-98.686
          c50.675,21.424,156.235,46.678,156.235,46.678c140.186-93.563,213.45-296.138,213.45-296.138
          c-14.515,3.99-28.395,5.652-41.475,5.652c-65.795,0-111-42.13-111-42.13l183.144-39.885C909.186,218.71,915.01,0,915.01,0
          L358.176,495.258C295.116,551.344,250.776,625.424,231.14,707.501z"/>
        </g>
        </svg>
      </div> 
    </div>
  );
}

export default App;

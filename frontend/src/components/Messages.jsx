import axios from 'axios';
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types'; // Ensure PropTypes is imported


const Message = ({ speed, angle }) => {
    // State to store the response data
    const [responseData, setResponseData] = useState(null);

    // State to handle loading status
    const [loading, setLoading] = useState(true);

    // State to handle error status
    const [error, setError] = useState(null);

    
    // Function to fetch data using Axios
    const fetchData = async () => {
        const requestData = {
            speed: speed,
            degrees: angle
        };



        try {
            // Make the GET request to the FastAPI backend
            const response = await axios.post('https://foresights-backend-720652506362.us-central1.run.app/ai/generate-description', requestData);

            
            // Store the response data in state

            var res = JSON.stringify(response.data.description.text)
            res = res.replace(/"/g, '')
            setResponseData(res); 
            
        } catch (err) {
            // Handle errors (e.g., network issues, server errors)
            console.error('Error fetching data:', err);
            setError(err);
        } finally {
            // Stop the loading state once the request is finished
            setLoading(false);
        }
    };

    // useEffect hook to fetch data when the component mounts
    useEffect(() => {
        fetchData();
    }, []); // Empty dependency array ensures this runs once after the component mounts

    return (
        <div >
            {loading && <p>Loading...</p>} {/* Show loading message while fetching data */}
            
            {error && <p>Error: {error.message}</p>} {/* Show error message if something went wrong */}

            {responseData && (
                <div className="w-72 h-36 border p-2 whitespace-normal"> 
                    {responseData} {/* Display fetched data */}
                </div>
            )}
        </div>
    );
};

Message.propTypes = {
    speed: PropTypes.number.isRequired, // Validate that speed is a number and is required
    angle: PropTypes.number.isRequired  // Validate that angle is a number and is required
};

export default Message;
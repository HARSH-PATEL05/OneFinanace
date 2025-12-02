import { useState, useEffect } from "react";
import style from "./Style/Contact.module.css";

function Contact() {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        message: ""
    });

    const [savedMessages, setSavedMessages] = useState([]);

    useEffect(() => {
        const data = localStorage.getItem("contactMessages");
        if (data) setSavedMessages(JSON.parse(data));
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();

        if (!formData.name || !formData.email || !formData.message) {
            alert("Please fill all fields.");
            return;
        }

        const newMessage = { ...formData, date: new Date().toLocaleString() };
        const updated = [...savedMessages, newMessage];

        localStorage.setItem("contactMessages", JSON.stringify(updated));
        setSavedMessages(updated);

        alert("Message Sent!");

        setFormData({ name: "", email: "", message: "" });
    };

    return (
        
            <div className={style.scrollArea}>
                
                {/* Top Info */}
                <div className={style.headerCard}>
                    <h1>Contact Me</h1>
                    <p className={style.subHead}>Let's connect & build something amazing.</p>

                    <div className={style.infoBox}>
                        <p><strong>Name:</strong> Harsh Patel</p>
                        <p><strong>Email:</strong> harsh60791@gmail.com</p>
                        <p><strong>Phone:</strong> +91 9340430152</p>
                    </div>
                </div>

                {/* ABOUT */}
                <div className={style.aboutCard}>
                    <h2>About OneFinance</h2>
                    <p>
                        OneFinance is your personal financial companion designed to analyze portfolios,
                        predict stock movements, monitor bank transactions, and provide intelligent insights with ease.
                        <br /><br />
                        Reach out for support, feedback, collaboration, or project inquiries.
                    </p>
                </div>

                {/* FORM */}
                <div className={style.formCard}>
                    <h2>Send a Message</h2>

                    <form onSubmit={handleSubmit} className={style.contactForm}>
                        <input
                            type="text"
                            placeholder="Your Name"
                            value={formData.name}
                            onChange={(e) =>
                                setFormData({ ...formData, name: e.target.value })
                            }
                        />

                        <input
                            type="email"
                            placeholder="Your Email"
                            value={formData.email}
                            onChange={(e) =>
                                setFormData({ ...formData, email: e.target.value })
                            }
                        />

                        <textarea
                            placeholder="Write your message..."
                            value={formData.message}
                            onChange={(e) =>
                                setFormData({ ...formData, message: e.target.value })
                            }
                        ></textarea>

                        <button type="submit">Send</button>
                    </form>
                </div>

                {/* FOOTER */}
                <div className={style.footer}>
                    © {new Date().getFullYear()} OneFinance — Built with ❤️ by Harsh Patel
                </div>
                </div>
           
        
    );
}

export default Contact;

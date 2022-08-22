"use strict";


// // Smooth scroll for float btn to navbar
// document.getElementById("float__btn").addEventListener("click", function (e) {
//   e.preventDefault();
//   document.querySelector(".navbar").scrollIntoView({ behavior: "smooth" });
// });

// // Show the float btn when the navbar move from viewport
// const floaterBtnContainer = document.getElementById("foat__btn__container");
// const navigationBar = document.querySelector(".navigation__bar");
// const obsCallback = function (entries) {
//   const [entry] = entries;
//   //   console.log(entry.target);
//   if (!entry.isIntersecting) floaterBtnContainer.classList.remove("hidden");
//   else floaterBtnContainer.classList.add("hidden");
//   //   if (!entry.isIntersecting) return;
//   //   entry.target.classList.remove("section--hidden");
//   //   observer.unobserve(entry.target);
// };
// const obsOptions = {
//   root: null,
//   threshold: 0,
// };
// const observer = new IntersectionObserver(obsCallback, obsOptions);
// observer.observe(navigationBar);

// /* copyright dynamic year */
//  document.getElementById("copyrightYear").innerHTML = new Date().getFullYear();

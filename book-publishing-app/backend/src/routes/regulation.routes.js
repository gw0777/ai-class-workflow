import express from 'express';
import {
  createRegulation,
  getAllRegulations,
  getRegulationById,
  updateRegulation,
  deleteRegulation,
  searchRegulations,
  getRegulationsByCategory,
  getRegulationsByCountry
} from '../controllers/regulation.controller.js';
import { authenticate } from '../middleware/auth.middleware.js';

const router = express.Router();

// 출판 규정 CRUD
router.post('/', authenticate, createRegulation);
router.get('/', getAllRegulations);
router.get('/search', searchRegulations);
router.get('/category/:category', getRegulationsByCategory);
router.get('/country/:country', getRegulationsByCountry);
router.get('/:id', getRegulationById);
router.put('/:id', authenticate, updateRegulation);
router.delete('/:id', authenticate, deleteRegulation);

export default router;
